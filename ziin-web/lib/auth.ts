import type { NextAuthOptions } from "next-auth";
import type { JWT } from "next-auth/jwt";
import DiscordProvider from "next-auth/providers/discord";

const discordClientId = (process.env.DISCORD_CLIENT_ID ?? "").trim();
const discordClientSecret = (process.env.DISCORD_CLIENT_SECRET ?? "").trim();

export const authOptions: NextAuthOptions = {
  pages: {
    signIn: "/",
    error: "/auth/popup-close"
  },
  providers: [
    DiscordProvider({
      clientId: discordClientId,
      clientSecret: discordClientSecret,
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
    async jwt({ token, account }) {
      const nextToken = token as JWT & { accessToken?: string };
      if (account?.access_token) {
        nextToken.accessToken = account.access_token;
      }
      return nextToken;
    }
  }
};
