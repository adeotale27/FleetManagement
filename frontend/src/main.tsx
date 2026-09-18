import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppRoutes } from "./App";
import { AuthContext } from "./auth";
import { api, getToken, setToken } from "./api/client";
import type { User } from "./types";
import "./styles/global.css";

const client = new QueryClient();

function Root() {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(!getToken());
  useEffect(() => {
    const token = getToken();
    if (!token) return;
    api<User>("/auth/me")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setReady(true));
  }, []);
  if (!ready) return <div className="state">Loading…</div>;
  return (
    <AuthContext.Provider
      value={{
        user,
        setUser,
        logout: () => {
          setToken(null);
          setUser(null);
        },
      }}
    >
      <AppRoutes
        onLogin={(token, next) => {
          setToken(token);
          setUser(next as User);
        }}
      />
    </AuthContext.Provider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Root />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
