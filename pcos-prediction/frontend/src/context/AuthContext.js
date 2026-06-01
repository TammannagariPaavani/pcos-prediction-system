import { createContext, useContext, useEffect, useState } from "react";
import { fetchCurrentUser, loginUser, logoutUser, refreshSession, registerUser } from "@/api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const logoutMarker =
      typeof window !== "undefined" ? window.sessionStorage.getItem("pcos-logged-out") : null;
    if (logoutMarker) {
      setUser(null);
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("pcos-user");
        window.sessionStorage.removeItem("pcos-logged-out");
      }
      setLoading(false);
      return;
    }

    const hydrate = async () => {
      try {
        const me = await fetchCurrentUser();
        setUser(me);
      } catch (error) {
        try {
          const refreshed = await refreshSession();
          setUser(refreshed.user);
        } catch (refreshError) {
          setUser(null);
          if (typeof window !== "undefined") {
            window.localStorage.removeItem("pcos-user");
          }
        }
      } finally {
        setLoading(false);
      }
    };

    hydrate();
  }, []);

  const handleLogin = async (payload) => {
    const response = await loginUser(payload);
    setUser(response.user);
    return response;
  };

  const handleRegister = async (payload) => {
    return registerUser(payload);
  };

  const handleLogout = async () => {
    try {
      await logoutUser();
    } finally {
      setUser(null);
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("pcos-user");
        window.sessionStorage.setItem("pcos-logged-out", "1");
      }
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login: handleLogin,
        register: handleRegister,
        logout: handleLogout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
