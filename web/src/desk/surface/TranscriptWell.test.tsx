import {cleanup, render, screen} from '@testing-library/react';
import {afterEach, expect, it} from 'vitest';
import {TranscriptWell} from './TranscriptWell';
import {InspectorFacts} from './patterns/PreferencePane';

afterEach(cleanup);
const name = 'web/src/review/Decision.ts: retain the saved result';

it('keeps an explicit object, including an intentional absence, ahead of initials', () => {
  const view=render(<InspectorFacts object={<img src="/project.png" alt="Project" />} name={name} rows={[]} />);
  expect(screen.getByAltText('Project')).toHaveAttribute('src','/project.png');
  view.rerender(<InspectorFacts object={null} name={name} rows={[]} />);
  expect(view.container.querySelector('.surface-inspector-object')).toBeNull();
  view.rerender(<InspectorFacts name={name} rows={[]} />);
  expect(view.container.querySelector('.surface-inspector-object img')).toHaveAttribute('src',expect.stringContaining('/artifact.png'));
  view.rerender(<InspectorFacts name="Priya Nair" rows={[]} />);
  expect(view.container.querySelector('.surface-inspector-object')).toHaveTextContent('PN');
});

it.each(['saved','live'])('uses the same reading seat and metadata in %s mode', mode => {
  const view=render(<TranscriptWell id="record" seat live={mode === 'live' ? false : undefined}
    segments={[{speaker:'Karol',start_time:7,text:'Keep the saved source in view.'}]} footer={<span>Kept</span>} />);
  const well=view.container.querySelector('.surface-transcript-well')!;
  expect(well).toHaveAttribute('data-seat');
  expect(well.querySelector('time')).toHaveTextContent('0:07');
  expect(well.querySelector('.transcript-speaker')).toHaveTextContent('Karol');
  expect(well.querySelector('p')).toHaveTextContent('Keep the saved source in view.');
  expect(well).toHaveTextContent('Kept');
  expect(well).toHaveAttribute('data-feedback-redact','true');
});

it('draws a time only once when a legacy speaker label already includes it', () => {
  const view=render(<TranscriptWell id="call" seat segments={[{speaker:'HoldSpeak · 0:07',timestamp:'0:07',text:'Read the source.'}]} />);
  expect(view.container.querySelector('time')).toHaveTextContent('0:07');
  expect(view.container.querySelector('.transcript-speaker')).toHaveTextContent(/^HoldSpeak$/);
});
