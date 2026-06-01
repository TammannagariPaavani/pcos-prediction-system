import { useEffect } from "react";
import { useRouter } from "next/router";
import { useAuth } from "@/context/AuthContext";

export default function HomePage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (loading) {
      return;
    }
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role === "patient") {
      router.replace("/patient");
      return;
    }
    if (user.role === "doctor") {
      router.replace("/doctor");
      return;
    }
    router.replace("/admin");
  }, [loading, router, user]);

  return <div className="flex min-h-screen items-center justify-center text-slate-600">Loading workspace...</div>;
}
