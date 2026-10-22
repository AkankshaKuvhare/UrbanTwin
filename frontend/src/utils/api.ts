/**
 * UrbanTwin Backend API Service.
 * Provides live real-time API integrations with fallback to mock research data.
 */

export interface SystemHealth {
  status: string;
  database?: string;
  postgis?: string;
}

export interface CorrelationResponse {
  method: string;
  station_id: string;
  active_variables: string[];
  matrix: Record<string, Record<string, number>>;
  target_summary: Array<{
    variable: string;
    label: string;
    category: string;
    observations: number;
    pearson_r: number;
    pearson_p_value: number;
    spearman_rho: number;
    kendall_tau: number;
    relationship_strength: string;
    direction: string;
    abs_pearson_r: number;
  }>;
  traffic_included: boolean;
}

export interface NetworkResponse {
  station_id: string;
  threshold: number;
  nodes: Array<{
    id: string;
    label: string;
    category: string;
    color: string;
    mean: number;
    std: number;
    missing_pct: number;
    observations: number;
    centrality: number;
  }>;
  edges: Array<{
    source: string;
    target: string;
    source_label: string;
    target_label: string;
    weight: number;
    correlation: number;
    edge_type: string;
    color: string;
    thickness: number;
  }>;
  stats: {
    node_count: number;
    edge_count: number;
    threshold: number;
    density: number;
  };
}

export interface ScatterResponse {
  x_variable?: string;
  y_variable: string;
  station_id: string;
  regression_stats: {
    x_variable?: string;
    y_variable?: string;
    x_label?: string;
    y_label?: string;
    category?: string;
    n_observations?: number;
    pearson_r?: number;
    r_squared?: number;
    slope?: number;
    intercept?: number;
    p_value?: number;
    std_err?: number;
  };
  all_pairs_summary: Array<any>;
  points: Array<{ x: number; y: number }>;
}

export interface SeasonalityResponse {
  target_variable: string;
  station_id: string;
  monthly: Array<{
    _month: number;
    month_name: string;
    count: number;
    mean: number;
    std: number;
    median: number;
    min: number;
    max: number;
  }>;
  weekly: Array<any>;
  day_of_week: Array<{
    _dow: number;
    day_name: string;
    count: number;
    mean: number;
    std: number;
    median: number;
    min: number;
    max: number;
  }>;
  month_dow_matrix: Record<string, Record<string, number>>;
}

export interface TimeSeriesResponse {
  frequency: string;
  station_id: string;
  variables: string[];
  total_intervals: number;
  data: Array<Record<string, any>>;
}

export const UrbanTwinAPI = {
  /** Fetch backend system health check */
  async getHealth(): Promise<SystemHealth> {
    const res = await fetch('/health');
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  },

  /** Fetch pairwise correlations */
  async getCorrelation(method: string = 'pearson', stationId?: string): Promise<CorrelationResponse> {
    const url = new URL('/api/v1/relationships/correlation', window.location.origin);
    url.searchParams.set('method', method);
    if (stationId && stationId !== 'all') url.searchParams.set('station_id', stationId);

    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`Correlation fetch failed: ${res.statusText}`);
    return res.json();
  },

  /** Fetch force-directed relationship network */
  async getNetwork(threshold: number = 0.20, stationId?: string): Promise<NetworkResponse> {
    const url = new URL('/api/v1/relationships/network', window.location.origin);
    url.searchParams.set('threshold', threshold.toString());
    if (stationId && stationId !== 'all') url.searchParams.set('station_id', stationId);

    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`Network fetch failed: ${res.statusText}`);
    return res.json();
  },

  /** Fetch scatter and OLS regression stats */
  async getScatter(xVar?: string, yVar: string = 'aqi', stationId?: string): Promise<ScatterResponse> {
    const url = new URL('/api/v1/relationships/scatter', window.location.origin);
    if (xVar) url.searchParams.set('x_var', xVar);
    url.searchParams.set('y_var', yVar);
    if (stationId && stationId !== 'all') url.searchParams.set('station_id', stationId);

    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`Scatter fetch failed: ${res.statusText}`);
    return res.json();
  },

  /** Fetch seasonality cyclics */
  async getSeasonality(target: string = 'aqi', stationId?: string): Promise<SeasonalityResponse> {
    const url = new URL('/api/v1/relationships/seasonality', window.location.origin);
    url.searchParams.set('target', target);
    if (stationId && stationId !== 'all') url.searchParams.set('station_id', stationId);

    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`Seasonality fetch failed: ${res.statusText}`);
    return res.json();
  },

  /** Fetch synchronized aggregated time series */
  async getTimeSeries(freq: string = 'W', stationId?: string): Promise<TimeSeriesResponse> {
    const url = new URL('/api/v1/relationships/timeseries', window.location.origin);
    url.searchParams.set('freq', freq);
    if (stationId && stationId !== 'all') url.searchParams.set('station_id', stationId);

    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`Time-series fetch failed: ${res.statusText}`);
    return res.json();
  },

  /** Fetch map metadata and coverage */
  async getMapMetadata(): Promise<any> {
    const res = await fetch('/api/v1/map');
    if (!res.ok) throw new Error(`Map metadata fetch failed: ${res.statusText}`);
    return res.json();
  },

  /** Fetch all stations latest readings */
  async getStations(stationId?: string): Promise<any> {
    const url = new URL('/api/v1/stations', window.location.origin);
    if (stationId && stationId !== 'all') url.searchParams.set('station_id', stationId);
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`Stations fetch failed: ${res.statusText}`);
    return res.json();
  },

  /** Fetch H3 zones */
  async getZones(limit: number = 251, minAqi?: number): Promise<any> {
    const url = new URL('/api/v1/zones', window.location.origin);
    url.searchParams.set('limit', limit.toString());
    if (minAqi !== undefined) url.searchParams.set('min_aqi', minAqi.toString());
    const res = await fetch(url.toString());
    if (!res.ok) throw new Error(`Zones fetch failed: ${res.statusText}`);
    return res.json();
  },

  /** Fetch detailed health and db status */
  async getDetailedHealth(): Promise<any> {
    const res = await fetch('/api/v1/health');
    if (!res.ok) throw new Error(`Detailed health check failed: ${res.statusText}`);
    return res.json();
  },

  /** Fetch simulator preset scenarios */
  async getSimulatorScenarios(): Promise<any> {
    const res = await fetch('/api/v1/simulator/scenarios');
    if (!res.ok) throw new Error(`Simulator scenarios fetch failed: ${res.statusText}`);
    return res.json();
  },

  /** Run simulator prediction */
  async predictSimulator(params: Record<string, any>): Promise<any> {
    const res = await fetch('/api/v1/simulator/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(`Simulator prediction failed: ${res.statusText}`);
    return res.json();
  },

  /** Reset simulator */
  async resetSimulator(): Promise<any> {
    const res = await fetch('/api/v1/simulator/reset', { method: 'POST' });
    if (!res.ok) throw new Error(`Simulator reset failed: ${res.statusText}`);
    return res.json();
  },
};
