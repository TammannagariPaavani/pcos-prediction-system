import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import { useAuth } from "@/context/AuthContext";

const initialRegister = {
  full_name: "",
  email: "",
  password: "",
  role: "patient",
  organization_name: ""
};

const initialLogin = {
  email: "",
  password: ""
};

export default function LoginPage() {
  const router = useRouter();
  const { user, loading, login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [loginValues, setLoginValues] = useState(initialLogin);
  const [registerValues, setRegisterValues] = useState(initialRegister);
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (loading) {
      return;
    }
    if (!user) {
      return;
    }
    router.replace(user.role === "patient" ? "/patient" : user.role === "doctor" ? "/doctor" : "/admin");
  }, [loading, router, user]);

  const handleAuth = async () => {
    setSubmitting(true);
    setFeedback("");
    try {
      if (mode === "login") {
        const response = await login(loginValues);
        setFeedback(`Welcome back, ${response.user.email}.`);
      } else {
        const payload = {
          ...registerValues,
          organization_name: null
        };
        await register(payload);
        setFeedback("Account created. You can sign in now.");
        setMode("login");
      }
    } catch (error) {
      setFeedback(error.response?.data?.error || error.message || "Authentication failed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid min-h-screen place-items-center px-4 py-12">
      <div className="grid w-full max-w-6xl overflow-hidden rounded-[36px] bg-white shadow-glow lg:grid-cols-[1.1fr_0.9fr]">
        <section className="bg-gradient-to-br from-pine via-[#146A75] to-[#E86A33] p-10 text-white">
          <p className="text-xs font-semibold uppercase tracking-[0.4em] text-white/75">PCOS Prediction System</p>
          <h1 className="mt-5 text-5xl leading-tight">A clinical decision layer for screening, tracking, and explainable risk.</h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-white/85">
            Review multi-factor PCOS likelihood, visualize SHAP drivers, and produce clinician-ready PDF reports from a single secure workspace.
          </p>
          <div className="mt-10 grid gap-4 md:grid-cols-2">
            <div className="rounded-[28px] border border-white/15 bg-white/10 p-5 backdrop-blur">
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-white/70">Patients</p>
              <p className="mt-3 text-3xl font-extrabold">Risk Gauge</p>
              <p className="mt-2 text-sm text-white/80">Live intake, explainable predictions, and downloadable reports.</p>
            </div>
            <div className="rounded-[28px] border border-white/15 bg-white/10 p-5 backdrop-blur">
              <p className="text-sm font-semibold uppercase tracking-[0.3em] text-white/70">Clinicians</p>
              <p className="mt-3 text-3xl font-extrabold">History Trends</p>
              <p className="mt-2 text-sm text-white/80">Longitudinal review for doctors and deployment controls for admins.</p>
            </div>
          </div>
        </section>

        <section className="bg-[#FCFAF7] p-8 md:p-10">
          <div className="mb-6 flex rounded-full bg-clay p-1">
            {["login", "register"].map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setMode(item)}
                className={`flex-1 rounded-full px-4 py-3 text-sm font-semibold capitalize transition ${
                  mode === item ? "bg-white text-pine shadow-sm" : "text-slate-500"
                }`}
              >
                {item}
              </button>
            ))}
          </div>

          <div className="space-y-4">
            {mode === "register" ? (
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-700">Full Name</span>
                <input
                  type="text"
                  value={registerValues.full_name}
                  onChange={(event) => setRegisterValues((current) => ({ ...current, full_name: event.target.value }))}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3"
                />
              </label>
            ) : null}
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-slate-700">Email</span>
              <input
                type="email"
                value={mode === "login" ? loginValues.email : registerValues.email}
                onChange={(event) =>
                  mode === "login"
                    ? setLoginValues((current) => ({ ...current, email: event.target.value }))
                    : setRegisterValues((current) => ({ ...current, email: event.target.value }))
                }
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-slate-700">Password</span>
              <input
                type="password"
                value={mode === "login" ? loginValues.password : registerValues.password}
                onChange={(event) =>
                  mode === "login"
                    ? setLoginValues((current) => ({ ...current, password: event.target.value }))
                    : setRegisterValues((current) => ({ ...current, password: event.target.value }))
                }
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3"
              />
            </label>
            {mode === "register" ? (
              <>
                <div className="rounded-2xl bg-clay/60 p-4 text-sm text-slate-600">
                  Public signup creates patient accounts only. Doctor and admin access is managed from the clinic
                  admin panel.
                </div>
              </>
            ) : null}

            <button
              type="button"
              onClick={handleAuth}
              disabled={submitting}
              className="mt-4 w-full rounded-full bg-pine px-5 py-4 text-sm font-bold uppercase tracking-[0.25em] text-white disabled:opacity-60"
            >
              {submitting ? "Working..." : mode === "login" ? "Sign In" : "Create Account"}
            </button>
            {feedback ? <div className="rounded-2xl bg-white p-4 text-sm text-slate-600 shadow-sm">{feedback}</div> : null}
          </div>
        </section>
      </div>
    </div>
  );
}
