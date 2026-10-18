"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { Session } from "@/lib/types";
import { decodeSession } from "./session";

export function useSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const revision = useRef(0);

  useEffect(() => {
    const current = ++revision.current;
    api<unknown>("session")
      .then((payload) => {
        if (revision.current === current) setSession(decodeSession(payload));
      })
      .catch((error) => {
        if (
          revision.current === current &&
          !(error instanceof ApiError && error.status === 401)
        )
          setError(error.message);
      })
      .finally(() => {
        if (revision.current === current) setLoading(false);
      });
    const expired = () => {
      ++revision.current;
      setSession(null);
      setError("Your session ended. Sign in to continue.");
    };
    window.addEventListener("relay:session-expired", expired);
    return () => {
      ++revision.current;
      window.removeEventListener("relay:session-expired", expired);
    };
  }, []);

  const signIn = useCallback((session: Session) => {
    ++revision.current;
    setError("");
    setSession(session);
    setLoading(false);
  }, []);
  async function signOut() {
    try {
      await api("logout", {});
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 401)) {
        setError((error as Error).message);
        return;
      }
    }
    ++revision.current;
    setSession(null);
    setError("");
  }
  return { session, loading, error, signIn, signOut, setSession, setError };
}
