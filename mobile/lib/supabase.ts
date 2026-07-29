// Stub — supabase client removed in Clerk migration (Task 5).
// settings.tsx still references this; Task 7 will migrate it.
// This stub prevents Metro bundler resolution failure during expo export.
export const supabase = {
  auth: {
    signInWithPassword: async (_opts: unknown) => ({ error: new Error('Supabase removed') }),
    signOut: async () => ({ error: null }),
  },
  from: (_table: string) => ({
    select: (_cols: string) => ({ data: null, error: new Error('Supabase removed') }),
    upsert: (_data: unknown) => ({ error: new Error('Supabase removed') }),
  }),
};
