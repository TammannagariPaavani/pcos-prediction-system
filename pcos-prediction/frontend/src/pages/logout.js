import { useEffect } from "react";
import { useAuth } from "@/context/AuthContext";

export default function LogoutPage() {
  const { logout } = useAuth();

  useEffect(() => {
    const clearSession = async () => {
      try {
        await logout();
      } catch (error) {
        // Best-effort logout: redirect even if the API call fails.
      } finally {
        if (typeof window !== "undefined") {
          window.localStorage.removeItem("pcos-user");
          window.location.replace("/login");
        }
      }
    };

    clearSession();
  }, [logout]);

  return (
    <div className="grid min-h-screen place-items-center px-4 text-slate-600">
      Redirecting to login...
    </div>
  );
}
