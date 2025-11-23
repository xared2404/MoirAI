/**
 * Background Job Search Service
 * Realiza búsquedas automáticas en segundo plano con amplia cobertura de palabras clave
 * Se integra con jobs-search.js para alimentar el catálogo de oportunidades
 */

class BackgroundJobSearchService {
    constructor() {
        this.isRunning = false;
        this.isSearching = false;
        this.currentBatchIndex = 0;
        this.allResults = [];
        this.searchBatches = [
            // Batch 1: Tecnología
            ['python', 'javascript', 'react', 'sql', 'nodejs', 'typescript', 'angular'],
            // Batch 2: Backend & Cloud
            ['backend', 'api', 'aws', 'docker', 'kubernetes', 'microservices'],
            // Batch 3: Frontend & UI
            ['frontend', 'html', 'css', 'vue', 'webdesign', 'ui', 'ux'],
            // Batch 4: Data & AI
            ['data', 'machine learning', 'analytics', 'big data', 'sql', 'python'],
            // Batch 5: Devops & Infrastructure
            ['devops', 'linux', 'networking', 'infrastructure', 'ci/cd'],
            // Batch 6: Mobile
            ['mobile', 'android', 'ios', 'flutter', 'react native'],
            // Batch 7: QA & Testing
            ['testing', 'qa', 'automation', 'selenium', 'quality assurance'],
            // Batch 8: Empleos generales
            ['empleo', 'trabajo', 'vacante', 'junior', 'senior'],
            // Batch 9: Habilidades blandas
            ['liderazgo', 'comunicación', 'gestión de proyectos', 'análisis'],
            // Batch 10: Sectores
            ['finanzas', 'marketing', 'recursos humanos', 'administración']
        ];
        this.batchDelay = 3000; // 3 segundos entre batches
        this.maxResultsPerBatch = 20;
    }

    /**
     * Iniciar búsqueda en segundo plano
     */
    async start() {
        if (this.isRunning) {
            console.log('⏸️ Búsqueda en segundo plano ya está activa');
            return;
        }

        this.isRunning = true;
        this.currentBatchIndex = 0;
        this.allResults = [];

        console.log('🔍 Iniciando búsqueda automática en segundo plano...');
        console.log(`📊 Total de batches: ${this.searchBatches.length}`);

        // ✨ NUEVO: Cargar cache existente ANTES de buscar
        try {
            const cachedJobs = await this.loadFromCache();
            if (cachedJobs && cachedJobs.length > 0) {
                this.allResults = cachedJobs;
                console.log(`✅ Cache cargado: ${cachedJobs.length} empleos disponibles`);
                
                // Disparar evento para mostrar datos inmediatamente
                window.dispatchEvent(new CustomEvent('cacheLoaded', {
                    detail: { jobs: cachedJobs, count: cachedJobs.length }
                }));
            } else {
                console.log('📦 No hay cache disponible, comenzando búsqueda...');
            }
        } catch (error) {
            console.warn('⚠️ Error al cargar cache:', error.message);
            // Continuar sin cache
        }

        // Ejecutar búsquedas en segundo plano
        this.executeNextBatch();
    }

    /**
     * Detener búsqueda en segundo plano
     */
    stop() {
        this.isRunning = false;
        this.isSearching = false;
        console.log('⏹️ Búsqueda en segundo plano detenida');
    }

    /**
     * Ejecutar siguiente batch de búsqueda
     */
    async executeNextBatch() {
        if (!this.isRunning || this.currentBatchIndex >= this.searchBatches.length) {
            if (this.currentBatchIndex >= this.searchBatches.length) {
                console.log('✅ Búsqueda en segundo plano completada');
                console.log(`📊 Total de empleos encontrados: ${this.allResults.length}`);
                
                // Notificar que data está lista
                window.dispatchEvent(new CustomEvent('backgroundJobsReady', {
                    detail: { jobs: this.allResults, count: this.allResults.length }
                }));
            }
            this.isRunning = false;
            return;
        }

        const keywords = this.searchBatches[this.currentBatchIndex];
        const batchNumber = this.currentBatchIndex + 1;

        console.log(`📦 Batch ${batchNumber}/${this.searchBatches.length}: ${keywords.join(', ')}`);

        try {
            // Búsqueda para cada keyword del batch
            for (const keyword of keywords) {
                if (!this.isRunning) break;

                await this.searchKeyword(keyword);
                
                // Pequeño delay entre keywords para no sobrecargar
                await this.delay(500);
            }

            // Incrementar índice y agendar siguiente batch
            this.currentBatchIndex++;

            if (this.isRunning) {
                // Esperar antes del siguiente batch
                console.log(`⏳ Esperando ${this.batchDelay}ms antes del siguiente batch...`);
                setTimeout(() => this.executeNextBatch(), this.batchDelay);
            }

        } catch (error) {
            console.error(`❌ Error en batch ${batchNumber}:`, error);
            
            // Continuar con siguiente batch a pesar del error
            this.currentBatchIndex++;
            setTimeout(() => this.executeNextBatch(), this.batchDelay);
        }
    }

    /**
     * Buscar por una palabra clave específica
     * ✨ MEJORADO: Usa más parámetros para búsquedas más relevantes
     */
    async searchKeyword(keyword) {
        if (this.isSearching) {
            // Si ya hay una búsqueda en progreso, esperar
            await this.waitForSearchComplete();
        }

        this.isSearching = true;

        try {
            // ✨ MEJORADO: Enviar más parámetros para mejor relevancia
            const response = await apiClient.post('/job-scraping/search', {
                keyword: keyword,
                detailed: true,           // Datos básicos (más rápido)
                sort_by: 'relevance',      // Ordenar por relevancia
                page: 1,
                // Parámetros opcionales para enriquecer búsquedas
                location: null,            // Se puede parametrizar después
                category: null,            // Categoría de trabajo
                experience_level: null,    // Nivel de experiencia
                work_mode: null,           // Modalidad (remoto, híbrido, presencial)
                job_type: null,            // Tipo de contrato
                company_verified: false    // Solo empresas verificadas
            });

            if (response.jobs && Array.isArray(response.jobs)) {
                // Filtrar duplicados por job_id
                const newJobs = response.jobs.slice(0, this.maxResultsPerBatch);
                const filteredJobs = newJobs.filter(job => 
                    !this.allResults.some(existing => existing.id === job.id || existing.job_id === job.job_id)
                );

                if (filteredJobs.length > 0) {
                    this.allResults.push(...filteredJobs);
                    
                    // ✨ NUEVO: Guardar en cache (no-blocking)
                    this.saveToCache(filteredJobs, keyword).catch(err => 
                        console.warn('⚠️ Error guardando cache:', err.message)
                    );
                    
                    console.log(`✅ "${keyword}": ${filteredJobs.length} empleos agregados (total: ${this.allResults.length})`);
                    
                    // Disparar evento para actualización en tiempo real
                    window.dispatchEvent(new CustomEvent('jobsUpdated', {
                        detail: { 
                            keyword: keyword,
                            newJobs: filteredJobs,
                            totalJobs: this.allResults.length
                        }
                    }));
                } else {
                    console.log(`⚪ "${keyword}": Sin empleos nuevos`);
                }
            }

        } catch (error) {
            console.warn(`⚠️ Error buscando "${keyword}":`, error.message);
            // No lanzar error, solo registrar y continuar
        } finally {
            this.isSearching = false;
        }
    }

    /**
     * Esperar a que se complete la búsqueda actual
     */
    async waitForSearchComplete() {
        return new Promise(resolve => {
            const checkInterval = setInterval(() => {
                if (!this.isSearching) {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 100);
            
            // Timeout de 10 segundos
            setTimeout(() => {
                clearInterval(checkInterval);
                resolve();
            }, 10000);
        });
    }

    /**
     * Helper: Delay
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Obtener resultados actuales
     */
    getResults() {
        return this.allResults;
    }

    /**
     * Obtener progreso
     */
    getProgress() {
        return {
            currentBatch: this.currentBatchIndex,
            totalBatches: this.searchBatches.length,
            percentage: Math.round((this.currentBatchIndex / this.searchBatches.length) * 100),
            totalJobs: this.allResults.length,
            isRunning: this.isRunning,
            isSearching: this.isSearching
        };
    }

    /**
     * Limpiar resultados
     */
    clear() {
        this.allResults = [];
        this.currentBatchIndex = 0;
        console.log('🧹 Resultados limpios');
    }

    /**
     * ✨ NUEVO: Cargar empleos del cache persistente (BD)
     */
    async loadFromCache() {
        try {
            const response = await apiClient.get('/job-scraping/cache/list', {
                params: {
                    limit: 500,
                    offset: 0
                }
            });

            if (response && response.jobs && Array.isArray(response.jobs)) {
                console.log(`📦 Cache cargado: ${response.jobs.length} de ${response.total} empleos disponibles`);
                return response.jobs;
            }
            return [];

        } catch (error) {
            console.warn('⚠️ No hay cache disponible:', error.message);
            return [];
        }
    }

    /**
     * ✨ NUEVO: Guardar empleos en cache persistente (BD) después de cada búsqueda
     */
    async saveToCache(jobs, keyword) {
        try {
            // ✅ Validación de entrada
            if (!jobs || jobs.length === 0) {
                console.warn('⚠️  Sin empleos para guardar en cache');
                return 0;
            }

            console.log(`💾 Guardando ${jobs.length} empleos en cache (keyword: "${keyword}")`);

            const response = await apiClient.post('/job-scraping/cache/store', {
                jobs: jobs,
                keyword: keyword,
                source: 'occ'
            });

            // ✅ Validación completa de respuesta
            if (!response) {
                console.error('❌ Respuesta vacía del endpoint cache/store');
                return 0;
            }

            if (response.saved_count && response.saved_count > 0) {
                console.log(`✅ Cache: ${response.saved_count} empleos guardados`);
                if (response.total_cached) {
                    console.log(`📊 Total en cache: ${response.total_cached}`);
                }
                return response.saved_count;
            } else {
                console.warn(`⚠️  Cache: 0 empleos guardados (posiblemente duplicados o existentes)`);
                return 0;
            }

        } catch (error) {
            console.error('❌ Error guardando cache:', error.message || error);
            // No lanzar error, solo loguear. El flujo debe continuar sin cache.
            return 0;
        }
    }
}

// Instancia global
const backgroundJobSearch = new BackgroundJobSearchService();
