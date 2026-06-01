import Link from "next/link";
import { useRouter } from "next/router";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";

const navItems = [
  { href: "/patient", label: "Patient Portal", roles: ["patient"] },
  { href: "/doctor", label: "Doctor Dashboard", roles: ["doctor", "admin"] },
  { href: "/admin", label: "Admin Panel", roles: ["admin"] }
];

export default function WorkspaceShell({ title, subtitle, children }) {
  const router = useRouter();
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const filteredNav = navItems.filter((item) => item.roles.includes(user?.role));

  return (
    <div className="isolate min-h-screen px-4 py-6 md:px-8">
      <div className="mx-auto max-w-7xl">
        <Link
          href="/logout"
          prefetch={false}
          className="hidden"
        >
          Log Out
        </Link>
        <form action="/logout" method="get" className="fixed right-4 top-4 z-[9999] m-0">
          <button
            type="submit"
            className="cursor-pointer rounded-full bg-ember px-5 py-3 text-sm font-semibold text-white shadow-lg"
          >
            Log Out
          </button>
        </form>
        <header className="panel sticky top-4 z-50 mb-6 flex flex-col gap-4 px-6 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.35em] text-ember/80">PCOS Intelligence Suite</p>
            <h1 className="mt-2 text-3xl text-ink">{title}</h1>
            <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-full bg-white/80 px-4 py-2 text-sm text-slate-600">
              <span className="font-semibold text-slate-800">{user?.full_name}</span>
              {user?.organization?.name ? ` · ${user.organization.name}` : ""}
            </div>
            {filteredNav.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                  router.pathname === item.href ? "bg-pine text-white" : "bg-white/80 text-slate-700 hover:bg-clay"
                }`}
              >
                {item.label}
              </Link>
            ))}
            <button
              type="button"
              onClick={toggleTheme}
              className="relative z-50 cursor-pointer rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700"
            >
              Theme: {theme}
            </button>
          </div>
        </header>
        {children}
      </div>
    </div>
  );
}
