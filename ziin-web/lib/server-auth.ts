import type { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";

type JwtWithAccessToken = {
  accessToken?: unknown;
};

export const getDiscordAccessToken = async (request: NextRequest): Promise<string | null> => {
  const token = (await getToken({ req: request })) as JwtWithAccessToken | null;
  if (!token || typeof token.accessToken !== "string" || !token.accessToken) {
    return null;
  }
  return token.accessToken;
};
