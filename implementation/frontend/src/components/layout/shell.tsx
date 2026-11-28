import { Header } from "./header";
import { MobileNav } from "./mobile-nav";
import { Sidebar } from "./sidebar";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="lg:ps-64">
        <Header />
        <main className="w-full max-w-[1920px] px-4 pb-24 pt-5 sm:px-6 lg:px-8 lg:pb-8">{children}</main>
      </div>
      <MobileNav />
    </div>
  );
}
