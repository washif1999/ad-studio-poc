import { NextRequest, NextResponse } from 'next/server';

const BACKEND_BASE = `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000'}/api/audio`;

/**
 * Proxy route: /api/video_stream/[...path]
 *
 * Purpose: Forward browser video requests (including Range headers) to the
 * FastAPI backend. Next.js rewrites do NOT forward the Range header, so
 * PIXI.js / HTML5 video never receives 206 Partial Content → video fails
 * to decode and nothing renders in the Shotstack canvas.
 *
 * This route manually proxies ALL request headers (including Range) so
 * 206 range responses are passed through intact.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const resolvedParams = await params;
  const filename = resolvedParams.path.join('/');
  const backendUrl = `${BACKEND_BASE}/${filename}`;

  // Forward all incoming headers to the backend (Range is critical for video)
  const forwardHeaders: Record<string, string> = {};
  request.headers.forEach((value, key) => {
    // Skip hop-by-hop headers that shouldn't be forwarded
    if (!['host', 'connection', 'transfer-encoding'].includes(key.toLowerCase())) {
      forwardHeaders[key] = value;
    }
  });

  let backendResponse: Response;
  try {
    backendResponse = await fetch(backendUrl, {
      method: 'GET',
      headers: forwardHeaders,
      // @ts-expect-error -- Node.js fetch supports this to disable body buffering
      duplex: 'half',
    });
  } catch (err) {
    return NextResponse.json(
      { error: `Backend unreachable: ${String(err)}` },
      { status: 502 },
    );
  }

  if (!backendResponse.ok && backendResponse.status !== 206 && backendResponse.status !== 304) {
    return NextResponse.json(
      { error: `Backend returned ${backendResponse.status}` },
      { status: backendResponse.status },
    );
  }

  // Forward all response headers from backend to browser
  const responseHeaders = new Headers();
  backendResponse.headers.forEach((value, key) => {
    // Allow everything through including Content-Range, Accept-Ranges
    responseHeaders.set(key, value);
  });

  // Ensure CORS headers are present so PIXI can read the response
  responseHeaders.set('Access-Control-Allow-Origin', '*');
  responseHeaders.set('Access-Control-Expose-Headers', 'Content-Range, Accept-Ranges, Content-Length');

  if (backendResponse.status === 304) {
    return new NextResponse(null, {
      status: 304,
      headers: responseHeaders,
    });
  }

  return new NextResponse(backendResponse.body, {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}

// Handle preflight OPTIONS requests
export async function OPTIONS() {
  return new NextResponse(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Range, Content-Type',
      'Access-Control-Max-Age': '86400',
    },
  });
}
