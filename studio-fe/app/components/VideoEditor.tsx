import React, { useEffect, useRef, useState } from 'react';
import { Edit, Canvas, Controls, Timeline, UIController } from '@shotstack/shotstack-studio';

interface VideoEditorProps {
  videoUrl: string;
}

export default function VideoEditor({ videoUrl }: VideoEditorProps) {
  const timelineRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const initialized = useRef(false);

  useEffect(() => {
    if (!timelineRef.current || !videoUrl || initialized.current) return;

    initialized.current = true;

    // Proxy through Next.js to bypass WebGL canvas taint restrictions.
    const filename = videoUrl.split('/').pop();
    const proxiedUrl = window.location.origin + '/api/video_stream/' + filename;

    const loadEditor = async () => {
      try {
        const template = {
          timeline: {
            tracks: [
              {
                clips: [
                  {
                    asset: { type: 'video', src: proxiedUrl, volume: 1 },
                    start: 0,
                    length: 15,
                  },
                ],
              },
            ],
          },
          output: { format: 'mp4', resolution: 'hd' },
        };

        // Per the official Shotstack SDK type definitions:
        //   constructor(edit: Edit)  — Canvas takes ONLY edit, no DOM arg.
        // The Canvas auto-discovers [data-shotstack-studio] in the DOM.
        // Correct load order (per official README): canvas.load() → edit.load()
        const edit = new Edit(template);
        const canvas = new Canvas(edit);

        await canvas.load();
        await edit.load();

        UIController.create(edit, canvas);

        // Timeline requires an explicit element reference.
        const timeline = new Timeline(edit, timelineRef.current!, { resizable: true });
        await timeline.load();

        const controls = new Controls(edit);
        await controls.load();
      } catch (err: any) {
        console.error('Shotstack Error:', err);
        setError('Failed to load Shotstack Studio. ' + err.message);
      }
    };

    loadEditor();
  }, [videoUrl]);

  if (error) {
    return <div style={{ color: 'red', padding: 20 }}>{error}</div>;
  }

  // CRITICAL STRUCTURE: [data-shotstack-studio] and [data-shotstack-timeline]
  // must be SIBLINGS — never nested. The Canvas mounts PIXI.js into the entire
  // [data-shotstack-studio] element. Nesting the timeline inside it causes the
  // WebGL renderer to break (child DOM nodes interfere with PIXI's canvas),
  // resulting in a blank canvas while audio still plays via Howler.js.
  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', backgroundColor: '#111', borderRadius: '8px', overflow: 'hidden', border: '1px solid #333' }}>

      {/* Canvas — Shotstack mounts PIXI.js WebGL here via [data-shotstack-studio] */}
      <div
        data-shotstack-studio
        style={{ flex: 1, minHeight: '500px', position: 'relative' }}
      />

      {/* Timeline — must be a SIBLING of [data-shotstack-studio], not a child */}
      <div
        ref={timelineRef}
        data-shotstack-timeline
        style={{ height: '300px', borderTop: '1px solid #333', backgroundColor: '#000' }}
      />

    </div>
  );
}
