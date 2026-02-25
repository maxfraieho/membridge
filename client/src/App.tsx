import { Switch, Route, Link, useLocation } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import RuntimeSettings from "@/pages/RuntimeSettings";
import MembridgePage from "@/pages/MembridgePage";

function NavBar() {
  const [location] = useLocation();

  const links = [
    { href: "/runtime", label: "Runtime" },
    { href: "/membridge", label: "Membridge" },
  ];

  return (
    <nav className="border-b bg-background" data-testid="nav-bar">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center h-14 gap-6">
          <span className="font-bold text-sm tracking-wide" data-testid="text-app-name">
            BLOOM
          </span>
          <div className="flex gap-1">
            {links.map(({ href, label }) => {
              const isActive = location === href || (href === "/runtime" && location === "/");
              return (
                <Link key={href} href={href}>
                  <span
                    data-testid={`nav-link-${label.toLowerCase()}`}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer ${
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:text-foreground hover:bg-muted"
                    }`}
                  >
                    {label}
                  </span>
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}

function Router() {
  return (
    <Switch>
      <Route path="/" component={RuntimeSettings} />
      <Route path="/runtime" component={RuntimeSettings} />
      <Route path="/membridge" component={MembridgePage} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <NavBar />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
