import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const projects = defineCollection({
  loader: glob({ base: './src/content/projects', pattern: '**/*.{md,mdx}' }),
  schema: z.object({
    title: z.string(),
    summary: z.string(),
    problem: z.string(),
    role: z.string(),
    technologies: z.array(z.string()),
    cover: z.string().optional(),
    repository: z.string().url().optional(),
    demo: z.string().url().optional(),
    featured: z.boolean().default(false),
  }),
});

export const collections = { projects };
