import { Clock, FileText, LayoutDashboard, Newspaper, Radio, Tags, type LucideIcon } from "lucide-react";

export interface NavItem { href: string; label: string; icon: LucideIcon; mobilePrimary: boolean }

export const NAV_ITEMS: NavItem[] = [
  { href: "/overview", label: "Overview", icon: LayoutDashboard, mobilePrimary: true },
  { href: "/stories", label: "Stories", icon: Newspaper, mobilePrimary: true },
  { href: "/articles", label: "Articles", icon: FileText, mobilePrimary: true },
  { href: "/sources", label: "Sources", icon: Radio, mobilePrimary: true },
  { href: "/categories", label: "Categories", icon: Tags, mobilePrimary: false },
  { href: "/time-activity", label: "Time Activity", icon: Clock, mobilePrimary: false },
];

export const isActiveRoute = (path: string, href: string) => path === href || path.startsWith(`${href}/`);
