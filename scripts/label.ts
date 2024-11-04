import { glob } from 'glob';
import fs from 'fs';
import z from 'zod';
import { parse } from 'jsonc-parser';

const files = glob.sync('**/*.jsonc');

const zLabel = z.object({
  meta: z.object({
    offset: z.number(),
    name: z.string(),
    count: z.number(),
    video_url: z.string().optional(),
    frames: z.number(),
    frame_rate: z.number(),
    type: z.union([z.literal('frame'), z.literal('time')]),
  }),
  labels: z.array(z.string()),
  label_range: z.array(
    z.object({
      start: z.number(),
      end: z.number(),
      label: z.number(),
    }),
  ),
});

files.forEach((file) => {
  const content = fs.readFileSync(file, 'utf-8');
  const { success, data } = zLabel.safeParse(parse(content));

  if (!success) {
    console.error(`Error in ${file}`);
    return;
  }

  const length = data.meta.frames;
  const otherLabel = data.labels.length + 1;
  const labels = Array.from({ length }, () => otherLabel);

  const { offset, frame_rate, type } = data.meta;
  data.label_range.forEach(({ start, end, label }) => {
    const rate = type === 'frame' ? 1 : frame_rate;

    const s = (start - offset) * rate;
    const e = (end - offset) * rate;
    for (let i = s; i < e; i++) labels[i] = label;
  });

  const outputFile = file.replace('.jsonc', '.csv');
  const output = labels.join('\n');
  fs.writeFileSync(outputFile, output);
});
