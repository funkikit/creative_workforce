import type { FetchCreateContextFnOptions } from "@trpc/server/adapters/fetch";

export async function createContext({ req }: FetchCreateContextFnOptions) {
  return {
    headers: req.headers,
  };
}

export type TrpcContext = Awaited<ReturnType<typeof createContext>>;

