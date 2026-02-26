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
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  Send,
  Play,
  Loader2,
  MessageSquare,
} from "lucide-react";

import type {
  WorkerNode,
  Lease,
  LLMTask,
  LLMResult,
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

function CreateTaskForm() {
  const { toast } = useToast();
  const [prompt, setPrompt] = useState("");
  const [contextId, setContextId] = useState("");
  const [agentSlug, setAgentSlug] = useState("default");
  const [desiredFormat, setDesiredFormat] = useState<"text" | "json">("text");
  const [autoDispatch, setAutoDispatch] = useState(true);

  const workersQuery = useQuery<WorkerNode[]>({
    queryKey: ["/api/runtime/workers"],
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const createRes = await apiRequest("POST", "/api/runtime/llm-tasks", {
        prompt: prompt.trim(),
        context_id: contextId.trim() || `ctx-${Date.now()}`,
        agent_slug: agentSlug.trim() || "default",
        desired_format: desiredFormat,
        policy: { timeout_sec: 120, budget: 0 },
      });
      const task = await createRes.json();

      if (autoDispatch && task.id) {
        try {
          const dispatchRes = await apiRequest("POST", `/api/runtime/llm-tasks/${task.id}/dispatch`);
          const dispatch = await dispatchRes.json();
          return { task, dispatch, dispatched: true };
        } catch (err: any) {
          return { task, dispatched: false, dispatchError: err.message };
        }
      }

      return { task, dispatched: false };
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/llm-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/leases"] });
      if (data.dispatched) {
        toast({
          title: "Task created & dispatched",
          description: `Task ${data.task.id.substring(0, 8)}... sent to worker for Claude CLI execution`,
        });
      } else if (data.dispatchError) {
        toast({
          title: "Task created, dispatch failed",
          description: data.dispatchError,
          variant: "destructive",
        });
      } else {
        toast({ title: "Task created", description: `ID: ${data.task.id.substring(0, 8)}...` });
      }
      setPrompt("");
    },
    onError: (err: Error) => {
      toast({ title: "Failed to create task", description: err.message, variant: "destructive" });
    },
  });

  const onlineWorkers = (workersQuery.data || []).filter(
    (w) => w.status === "online" && w.capabilities?.claude_cli
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Create Claude CLI Task
        </CardTitle>
        <CardDescription>
          Send a prompt to be executed via Claude CLI on a worker node.
          {onlineWorkers.length > 0 ? (
            <span className="text-green-600 dark:text-green-400 ml-1">
              {onlineWorkers.length} worker(s) with Claude CLI online
            </span>
          ) : (
            <span className="text-destructive ml-1">
              No workers with Claude CLI available
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="task-prompt">Prompt</Label>
            <Textarea
              id="task-prompt"
              data-testid="input-task-prompt"
              placeholder="Enter your prompt for Claude CLI..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={4}
              className="font-mono text-sm"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="task-context">Context ID</Label>
              <Input
                id="task-context"
                data-testid="input-task-context"
                placeholder="auto-generated"
                value={contextId}
                onChange={(e) => setContextId(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Same context ID = same session memory
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="task-agent">Agent Slug</Label>
              <Input
                id="task-agent"
                data-testid="input-task-agent"
                placeholder="default"
                value={agentSlug}
                onChange={(e) => setAgentSlug(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Maps to CLAUDE_PROJECT_ID
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="task-format">Output Format</Label>
              <Select value={desiredFormat} onValueChange={(v) => setDesiredFormat(v as "text" | "json")}>
                <SelectTrigger data-testid="select-task-format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="text">Text</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Button
              data-testid="button-create-task"
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending || !prompt.trim() || onlineWorkers.length === 0}
            >
              {createMutation.isPending ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Executing...</>
              ) : autoDispatch ? (
                <><Send className="h-4 w-4 mr-2" />Create & Dispatch</>
              ) : (
                <><Play className="h-4 w-4 mr-2" />Create Task</>
              )}
            </Button>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                data-testid="checkbox-auto-dispatch"
                checked={autoDispatch}
                onChange={(e) => setAutoDispatch(e.target.checked)}
                className="rounded"
              />
              Auto-dispatch to worker
            </label>
          </div>
        </div>
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

  const dispatchMutation = useMutation({
    mutationFn: async (taskId: string) => {
      const res = await apiRequest("POST", `/api/runtime/llm-tasks/${taskId}/dispatch`);
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/llm-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["/api/runtime/leases"] });
      toast({
        title: data.dispatched ? "Task dispatched" : "Dispatch failed",
        description: data.dispatched
          ? `Sent to worker ${data.worker_id}`
          : data.error,
        variant: data.dispatched ? "default" : "destructive",
      });
    },
    onError: (err: Error) => {
      toast({ title: "Dispatch failed", description: err.message, variant: "destructive" });
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
                <TableHead>Prompt</TableHead>
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
                  <TableCell className="max-w-[200px]">
                    <span className="text-xs text-muted-foreground truncate block" title={t.prompt}>
                      {t.prompt.length > 60 ? `${t.prompt.substring(0, 60)}...` : t.prompt}
                    </span>
                  </TableCell>
                  <TableCell>{statusBadge(t.status)}</TableCell>
                  <TableCell>{t.worker_id || "—"}</TableCell>
                  <TableCell>{t.attempts}/{t.max_attempts}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {formatRelative(t.created_at)}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {t.status === "queued" && (
                        <Button
                          data-testid={`button-dispatch-${t.id}`}
                          variant="outline"
                          size="sm"
                          onClick={() => dispatchMutation.mutate(t.id)}
                          disabled={dispatchMutation.isPending}
                          title="Dispatch to worker for Claude CLI execution"
                        >
                          {dispatchMutation.isPending ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <Send className="h-3 w-3" />
                          )}
                        </Button>
                      )}
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
                    </div>
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
            <CreateTaskForm />
            <Separator />
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
