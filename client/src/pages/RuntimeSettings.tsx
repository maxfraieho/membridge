import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { queryClient, apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import {
  Server,
  Plug,
  Activity,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  Cpu,
  BarChart3,
} from "lucide-react";

import type {
  WorkerNode,
  Lease,
  LLMTask,
  RuntimeConfig,
} from "@shared/schema";

function statusBadge(status: string) {
  const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
    online: "default",
    offline: "secondary",
    syncing: "outline",
    error: "destructive",
    unknown: "secondary",
    active: "default",
    expired: "secondary",
    released: "outline",
    failed: "destructive",
    queued: "outline",
    leased: "default",
    running: "default",
    completed: "default",
    dead: "destructive",
  };
  return (
    <Badge data-testid={`badge-status-${status}`} variant={variants[status] || "secondary"}>
      {status}
    </Badge>
  );
}

function formatTime(ts: number | null) {
  if (!ts) return "—";
  return new Date(ts).toLocaleString();
}

function formatRelative(ts: number | null) {
  if (!ts) return "—";
  const diff = Date.now() - ts;
  if (diff < 60000) return `${Math.round(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.round(diff / 60000)}m ago`;
  return `${Math.round(diff / 3600000)}h ago`;
}

function ConnectionConfig() {
  const { toast } = useToast();
  const [url, setUrl] = useState("");
  const [key, setKey] = useState("");

  const configQuery = useQuery<RuntimeConfig>({
    queryKey: ["/api/runtime/config"],
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/runtime/config", {
        membridge_server_url: url || configQuery.data?.membridge_server_url,
        admin_key: key,
      });
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/config"] });
      toast({ title: "Configuration saved" });
      setKey("");
    },
    onError: (err: Error) => {
      toast({ title: "Save failed", description: err.message, variant: "destructive" });
    },
  });

  const testMutation = useMutation({
    mutationFn: async () => {
      const res = await apiRequest("POST", "/api/runtime/test-connection");
      return res.json();
    },
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/config"] });
      if (data.connected) {
        toast({ title: "Connection successful", description: `Version: ${data.health?.version || "unknown"}` });
      } else {
        toast({ title: "Connection failed", description: data.error, variant: "destructive" });
      }
    },
    onError: (err: Error) => {
      toast({ title: "Test failed", description: err.message, variant: "destructive" });
    },
  });

  const config = configQuery.data;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plug className="h-5 w-5" />
          Membridge Control Plane Connection
        </CardTitle>
        <CardDescription>
          Configure the connection to the Membridge control plane server.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2 text-sm">
          {config?.connected ? (
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          ) : (
            <XCircle className="h-4 w-4 text-red-500" />
          )}
          <span data-testid="text-connection-status">
            {config?.connected ? "Connected" : "Not connected"}
          </span>
          {config?.last_test && (
            <span className="text-muted-foreground ml-2">
              Last tested: {formatRelative(config.last_test)}
            </span>
          )}
        </div>

        <div className="grid gap-4 max-w-lg">
          <div className="space-y-2">
            <Label htmlFor="membridge-url">Server URL</Label>
            <Input
              id="membridge-url"
              data-testid="input-membridge-url"
              placeholder={config?.membridge_server_url || "http://127.0.0.1:8000"}
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="admin-key">Admin Key</Label>
            <Input
              id="admin-key"
              data-testid="input-admin-key"
              type="password"
              placeholder={config?.admin_key_masked || "Enter admin key"}
              value={key}
              onChange={(e) => setKey(e.target.value)}
            />
          </div>
          <div className="flex gap-2">
            <Button
              data-testid="button-save-config"
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending || (!url && !key)}
            >
              {saveMutation.isPending ? "Saving..." : "Save"}
            </Button>
            <Button
              data-testid="button-test-connection"
              variant="outline"
              onClick={() => testMutation.mutate()}
              disabled={testMutation.isPending}
            >
              {testMutation.isPending ? "Testing..." : "Test Connection"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function WorkersTable() {
  const workersQuery = useQuery<WorkerNode[]>({
    queryKey: ["/api/runtime/workers"],
    refetchInterval: 15000,
  });

  const workers = workersQuery.data || [];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            Workers Online
          </CardTitle>
          <Button
            data-testid="button-refresh-workers"
            variant="ghost"
            size="sm"
            onClick={() => queryClient.invalidateQueries({ queryKey: ["/api/runtime/workers"] })}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>
          {workers.length} worker(s) registered
        </CardDescription>
      </CardHeader>
      <CardContent>
        {workersQuery.isLoading ? (
          <div className="text-sm text-muted-foreground py-4" data-testid="text-workers-loading">Loading workers...</div>
        ) : workers.length === 0 ? (
          <div className="text-sm text-muted-foreground py-4" data-testid="text-workers-empty">
            No workers registered. Start a membridge-agent on a machine to see it here.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Node</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Labels</TableHead>
                <TableHead>Concurrency</TableHead>
                <TableHead>Active Leases</TableHead>
                <TableHead>Last Heartbeat</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {workers.map((w) => (
                <TableRow key={w.id} data-testid={`row-worker-${w.id}`}>
                  <TableCell className="font-medium">{w.node_id}</TableCell>
                  <TableCell>{statusBadge(w.status)}</TableCell>
                  <TableCell>
                    {w.capabilities.labels.length > 0
                      ? w.capabilities.labels.map((l) => (
                          <Badge key={l} variant="outline" className="mr-1">{l}</Badge>
                        ))
                      : <span className="text-muted-foreground">—</span>
                    }
                  </TableCell>
                  <TableCell>{w.capabilities.max_concurrency}</TableCell>
                  <TableCell>{w.active_leases}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatRelative(w.last_heartbeat)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function LeasesTable() {
  const leasesQuery = useQuery<Lease[]>({
    queryKey: ["/api/runtime/leases"],
    refetchInterval: 10000,
  });

  const leases = leasesQuery.data || [];
  const activeLeases = leases.filter((l) => l.status === "active");

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" />
          Active Leases
        </CardTitle>
        <CardDescription>
          {activeLeases.length} active lease(s)
        </CardDescription>
      </CardHeader>
      <CardContent>
        {leasesQuery.isLoading ? (
          <div className="text-sm text-muted-foreground py-4">Loading leases...</div>
        ) : activeLeases.length === 0 ? (
          <div className="text-sm text-muted-foreground py-4" data-testid="text-leases-empty">
            No active leases.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Task ID</TableHead>
                <TableHead>Worker</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Expires</TableHead>
                <TableHead>Last Heartbeat</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {activeLeases.map((l) => (
                <TableRow key={l.id} data-testid={`row-lease-${l.id}`}>
                  <TableCell className="font-mono text-xs">
                    {l.task_id.substring(0, 8)}...
                  </TableCell>
                  <TableCell>{l.worker_id}</TableCell>
                  <TableCell>{statusBadge(l.status)}</TableCell>
                  <TableCell>{formatTime(l.started_at)}</TableCell>
                  <TableCell>{formatTime(l.expires_at)}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatRelative(l.last_heartbeat)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function TasksQueue() {
  const { toast } = useToast();

  const tasksQuery = useQuery<LLMTask[]>({
    queryKey: ["/api/runtime/llm-tasks"],
    refetchInterval: 10000,
  });

  const requeueMutation = useMutation({
    mutationFn: async (taskId: string) => {
      const res = await apiRequest("POST", `/api/runtime/llm-tasks/${taskId}/requeue`);
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/llm-tasks"] });
      toast({ title: "Task requeued" });
    },
    onError: (err: Error) => {
      toast({ title: "Requeue failed", description: err.message, variant: "destructive" });
    },
  });

  const tasks = tasksQuery.data || [];

  const counts: Record<string, number> = {};
  for (const t of tasks) {
    counts[t.status] = (counts[t.status] || 0) + 1;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            Task Queue
          </CardTitle>
          <Button
            data-testid="button-refresh-tasks"
            variant="ghost"
            size="sm"
            onClick={() => queryClient.invalidateQueries({ queryKey: ["/api/runtime/llm-tasks"] })}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription>
          <span className="flex gap-3 flex-wrap mt-1">
            {Object.entries(counts).map(([status, count]) => (
              <span key={status} data-testid={`text-task-count-${status}`}>
                {status}: <strong>{count}</strong>
              </span>
            ))}
            {tasks.length === 0 && "No tasks"}
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        {tasksQuery.isLoading ? (
          <div className="text-sm text-muted-foreground py-4">Loading tasks...</div>
        ) : tasks.length === 0 ? (
          <div className="text-sm text-muted-foreground py-4" data-testid="text-tasks-empty">
            No tasks in queue.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Task ID</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Worker</TableHead>
                <TableHead>Attempts</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {tasks.slice(0, 50).map((t) => (
                <TableRow key={t.id} data-testid={`row-task-${t.id}`}>
                  <TableCell className="font-mono text-xs">
                    {t.id.substring(0, 8)}...
                  </TableCell>
                  <TableCell>{t.agent_slug}</TableCell>
                  <TableCell>{statusBadge(t.status)}</TableCell>
                  <TableCell>{t.worker_id || "—"}</TableCell>
                  <TableCell>{t.attempts}/{t.max_attempts}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatRelative(t.created_at)}
                  </TableCell>
                  <TableCell>
                    {(t.status === "failed" || t.status === "dead") && (
                      <Button
                        data-testid={`button-requeue-${t.id}`}
                        variant="outline"
                        size="sm"
                        onClick={() => requeueMutation.mutate(t.id)}
                        disabled={requeueMutation.isPending}
                      >
                        Requeue
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function StatsOverview() {
  const statsQuery = useQuery<{
    tasks: { total: number; by_status: Record<string, number> };
    leases: { total: number; active: number };
    workers: { total: number; online: number };
  }>({
    queryKey: ["/api/runtime/stats"],
    refetchInterval: 15000,
  });

  const stats = statsQuery.data;

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <Server className="h-8 w-8 text-muted-foreground" />
            <div>
              <p className="text-2xl font-bold" data-testid="text-stat-workers">
                {stats?.workers.online ?? "—"} / {stats?.workers.total ?? "—"}
              </p>
              <p className="text-sm text-muted-foreground">Workers online</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <Activity className="h-8 w-8 text-muted-foreground" />
            <div>
              <p className="text-2xl font-bold" data-testid="text-stat-leases">
                {stats?.leases.active ?? "—"}
              </p>
              <p className="text-sm text-muted-foreground">Active leases</p>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-3">
            <BarChart3 className="h-8 w-8 text-muted-foreground" />
            <div>
              <p className="text-2xl font-bold" data-testid="text-stat-tasks">
                {stats?.tasks.total ?? "—"}
              </p>
              <p className="text-sm text-muted-foreground">Total tasks</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function RuntimeSettings() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-2xl font-bold" data-testid="text-page-title">Runtime Settings</h1>
          <p className="text-muted-foreground mt-1">
            BLOOM Runtime — Membridge Proxy configuration and monitoring
          </p>
        </div>

        <Tabs defaultValue="proxy" className="space-y-6">
          <TabsList data-testid="tabs-runtime">
            <TabsTrigger value="proxy" data-testid="tab-proxy">Membridge Proxy</TabsTrigger>
            <TabsTrigger value="tasks" data-testid="tab-tasks">Task Queue</TabsTrigger>
            <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
          </TabsList>

          <TabsContent value="proxy" className="space-y-6">
            <ConnectionConfig />
            <Separator />
            <WorkersTable />
            <Separator />
            <LeasesTable />
          </TabsContent>

          <TabsContent value="tasks" className="space-y-6">
            <TasksQueue />
          </TabsContent>

          <TabsContent value="overview" className="space-y-6">
            <StatsOverview />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
