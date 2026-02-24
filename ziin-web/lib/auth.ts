import type { NextAuthOptions } from "next-auth";
import type { JWT } from "next-auth/jwt";
import DiscordProvider from "next-auth/providers/discord";

export const authOptions: NextAuthOptions = {
  pages: {
    signIn: "/",
    error: "/"
  },
  providers: [
    DiscordProvider({
      clientId: process.env.DISCORD_CLIENT_ID ?? "",
      clientSecret: process.env.DISCORD_CLIENT_SECRET ?? "",
      authorization: {
        params: {
          scope: "identify email guilds"
        }
      }
    })
  ],
  session: {
    strategy: "jwt"
  },
  callbacks: {
    async redirect({ url, baseUrl }) {
      if (url.startsWith("/")) {
        return `${baseUrl}${url}`;
      }

      if (url.startsWith(baseUrl)) {
        return url;
      }

      return baseUrl;
    },
    async jwt({ token, account }) {
      const nextToken = token as JWT & { accessToken?: string };
      if (account?.access_token) {
        nextToken.accessToken = account.access_token;
      }
      return nextToken;
    }
  }
};
