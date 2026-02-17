<template>
  <div class="sensor-table-container">
    <div class="table-header">
      <h2>Sensor Data</h2>
    </div>

    <!-- Controls for filtering, searching, sorting -->
    <div class="controls-section">
      <div class="control-group">
        <label>Search by name:</label>
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="Enter sensor name..."
          @input="fetchSensors"
          class="search-input"
        />
      </div>

      <div class="control-group">
        <label>Filter by type:</label>
        <select 
          v-model="selectedType" 
          @change="fetchSensors"
          class="filter-select"
        >
          <option value="">-- All types --</option>
          <option v-for="type in sensorTypes" :key="type" :value="type">
            {{ type }}
          </option>
        </select>
      </div>

      <div class="control-group">
        <label>Sort by:</label>
        <select 
          v-model="sortBy" 
          @change="fetchSensors"
          class="filter-select"
        >
          <option value="sensor_name">By name</option>
          <option value="type">By type</option>
          <option value="id">By ID</option>
          <option v-for="metricKey in availableMetrics" :key="metricKey" :value="metricKey">
            {{ metricKey }}
          </option>
        </select>
        <select 
          v-model="sortOrder" 
          @change="fetchSensors"
          class="filter-select"
        >
          <option value="asc">Ascending ↑</option>
          <option value="desc">Descending ↓</option>
        </select>
      </div>

      <div class="control-group">
        <label>Show metrics:</label>
        <button @click="toggleMetricsPanel" class="toggle-metrics-btn">
          {{ showMetricsPanel ? 'Hide' : 'Show' }} metrics selection
        </button>
      </div>
    </div>

    <!-- Metrics selection -->
    <div v-if="showMetricsPanel" class="metrics-panel">
      <h3>Select metrics to display:</h3>
      <div class="metrics-grid">
        <label v-for="metric in availableMetrics" :key="metric" class="metric-checkbox">
          <input 
            type="checkbox" 
            :value="metric" 
            v-model="selectedMetrics"
            @change="fetchSensors"
          />
          {{ metric }}
        </label>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading sensor data...</p>
    </div>

    <!-- Error state -->
    <div v-if="error" class="error-state" role="alert" aria-live="assertive">
      <div class="error-text">
        <strong>Error:</strong> {{ error }}
      </div>
      <button class="retry-btn" @click="fetchSensors">Retry</button>
    </div>

    <!-- DataTable (only when not loading and no error) -->
    <DataTable 
      v-if="!loading && !error"
      :value="sensors" 
      showGridlines 
      tableStyle="min-width: 50rem"
      stripedRows
      class="sensor-datatable"
      scrollable
      scrollHeight="600px"
    >
      <!-- Static columns -->
      <Column field="id" header="ID" style="width: 8%; min-width: 50px"></Column>
      <Column field="sensor_name" header="Sensor Name" style="width: 20%; min-width: 150px"></Column>
      <Column field="type" header="Type" style="width: 20%; min-width: 150px"></Column>
      
      <!-- Dynamic measurement columns -->
      <Column 
        v-for="metricKey in displayedMetrics" 
        :key="metricKey"
        :field="`measurements.${metricKey}`"
        :header="metricKey"
        style="width: 13%; min-width: 120px"
      >
        <template #body="slotProps">
          <span class="metric-value">
            {{ formatNumber(slotProps.data?.measurements?.[metricKey]) }}
          </span>
        </template>
      </Column>
    </DataTable>

    <!-- No data message -->
    <div v-if="!loading && sensors.length === 0" class="no-data">
      <p>No data found. Change filters and try again.</p>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';

export default {
  components: {
    DataTable,
    Column,
  },
  data() {
    return {
      sensors: [],
      availableMetrics: [],
      sensorTypes: [],
      searchQuery: '',
      selectedType: '',
      selectedMetrics: [],
      sortBy: 'sensor_name',
      sortOrder: 'asc',
      showMetricsPanel: false,
      loading: false,
      error: null,
      apiBase: import.meta.env?.VITE_API_BASE || '',
    };
  },
  computed: {
    displayedMetrics() {
      if (this.selectedMetrics.length === 0) {
        return this.availableMetrics;
      }
      return this.selectedMetrics.filter(m => this.availableMetrics.includes(m));
    },
  },
  mounted() {
    this.fetchSensors();
  },
  methods: {
    async fetchSensors() {
      try {
        this.loading = true;
        this.error = null;          
        this.sensors = [];

        const params = { sort_by: this.sortBy, sort_order: this.sortOrder };
        if (this.searchQuery) params.search = this.searchQuery;
        if (this.selectedType) params.filter_type = this.selectedType;
        if (this.selectedMetrics.length > 0) params.metrics = this.selectedMetrics.join(',');

        const base = (this.apiBase || '').replace(/\/$/, '');
        const url = base
          ? (base.endsWith('/api') ? `${base}/sensors` : `${base}/api/sensors`)
          : '/api/sensors';

        const response = await axios.get(url, { params });
        const data = response?.data;

        if (!Array.isArray(data)) {
          console.error('Unexpected API response for /api/sensors:', data);
          this.sensors = [];
          this.error = 'Server returned unexpected data'; 
        } else {
          this.sensors = data;
          this.extractMetricKeysAndTypes();
          this.error = null;
        }
      } catch (error) {
        console.error('Error fetching sensors:', error);
        this.error = error?.message || 'Failed to load sensor data. Please try again.'; // draudzīgs teksts
      } finally {
        this.loading = false;
      }
    },

    extractMetricKeysAndTypes() {
      if (!Array.isArray(this.sensors)) {
        this.availableMetrics = [];
        this.sensorTypes = [];
        return;
      }
      const currentKeys = new Set();
      this.sensors.forEach(sensor => {
        if (sensor.measurements) {
          Object.keys(sensor.measurements).forEach(k => currentKeys.add(k));
        }
      });

      const merged = new Set([...(this.availableMetrics || []), ...Array.from(currentKeys)]);
      this.availableMetrics = Array.from(merged).sort();

      const mergedTypes = new Set([...(this.sensorTypes || [])]);
      this.sensors.forEach(sensor => {
        if (sensor.type && sensor.type !== 'n/a') mergedTypes.add(sensor.type);
      });
      this.sensorTypes = Array.from(mergedTypes).sort();

      
      if (this.selectedMetrics.length === 0) {
        this.selectedMetrics = [...this.availableMetrics];
      } else {
        
        this.selectedMetrics = this.selectedMetrics.filter(m => this.availableMetrics.includes(m));
      }

    
    },

    getMeasurement(sensor, metricKey) {
      return sensor && sensor.measurements ? sensor.measurements[metricKey] : undefined;
    },

    
    formatNumber(value) {
      if (value === null || value === undefined) return 'N/A';
      if (typeof value === 'string' && value.trim() === '') return 'N/A';

      const num = (typeof value === 'number') ? value : Number(value);
      return Number.isFinite(num) ? num.toFixed(2) : 'N/A';
    },

    toggleMetricsPanel() {
      this.showMetricsPanel = !this.showMetricsPanel;
    },
  },
};
</script>