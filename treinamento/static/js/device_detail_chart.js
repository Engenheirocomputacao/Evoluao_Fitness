/**
 * Device Detail Chart - JavaScript puro sem sintaxe Django
 * Inicializa e gerencia o gráfico de leituras do dispositivo IoT
 */

function initDeviceChart() {
    console.log('=== INICIALIZANDO GRÁFICO DO DISPOSITIVO ===');

    // Verificar se Chart.js está disponível com retry
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js ainda não carregado, tentando novamente em 200ms...');
        setTimeout(initDeviceChart, 200);
        return;
    }
    console.log('Chart.js versão:', Chart.version);

    // Obter dados do atributo data-leituras do container
    const chartContainer = document.querySelector('.chart-container');
    if (!chartContainer) {
        console.error('Container do gráfico não encontrado!');
        return;
    }

    // Obter tipo de dispositivo
    const deviceType = chartContainer.dataset.deviceType;
    console.log('Tipo de dispositivo:', deviceType);

    // Ler e parsear os dados JSON do atributo data-leituras
    let leituras;
    try {
        const leiturasRaw = chartContainer.dataset.leituras;
        if (!leiturasRaw) {
            console.warn('Atributo data-leituras não encontrado');
            showNoDataMessage();
            return;
        }
        leituras = JSON.parse(leiturasRaw);
        console.log('Leituras recebidas:', leituras);
        console.log('Quantidade de leituras:', leituras ? leituras.length : 0);
    } catch (erro) {
        console.error('Erro ao parsear JSON das leituras:', erro);
        showNoDataMessage();
        return;
    }

    // Validar dados
    if (!Array.isArray(leituras)) {
        console.error('Leituras não é um array válido');
        showNoDataMessage();
        return;
    }

    if (leituras.length === 0) {
        console.log('Nenhuma leitura disponível');
        showNoDataMessage();
        return;
    }

    // Filtrar dados válidos
    const dadosValidos = leituras.filter(function (item) {
        return item &&
            typeof item.valor === 'number' &&
            !isNaN(item.valor) &&
            item.timestamp &&
            typeof item.timestamp === 'string';
    });

    console.log('Dados válidos filtrados:', dadosValidos);
    console.log('Quantidade de dados válidos:', dadosValidos.length);

    if (dadosValidos.length === 0) {
        console.log('Nenhum dado válido encontrado');
        showNoDataMessage();
        return;
    }

    // Criar gráfico específico baseado no tipo de dispositivo
    switch (deviceType) {
        case 'heartrate':
            createHeartRateChart(dadosValidos);
            break;
        case 'steps':
            createStepsChart(dadosValidos);
            break;
        case 'reps':
            createRepsChart(dadosValidos);
            break;
        default:
            createDefaultChart(dadosValidos);
    }
}

/**
 * Gráfico padrão (linha) para dispositivos genéricos
 */
function createDefaultChart(dadosValidos) {
    const canvas = document.getElementById('readingsChart');
    if (!canvas) {
        console.error('Canvas não encontrado!');
        return;
    }

    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('Não foi possível obter contexto 2D');
        return;
    }

    console.log('Criando gráfico padrão...');

    try {
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dadosValidos.map(function (d) { return d.timestamp; }),
                datasets: [{
                    label: 'Medições',
                    data: dadosValidos.map(function (d) { return d.valor; }),
                    borderColor: 'rgb(99, 102, 241)',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: 'rgb(99, 102, 241)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        console.log('✅ Gráfico padrão criado com sucesso!', chart);
        console.log('📊 Dados plotados:', dadosValidos.length, 'pontos');

    } catch (erro) {
        console.error('❌ Erro ao criar gráfico:', erro);
        console.error('Stack trace:', erro.stack);
        showNoDataMessage();
    }
}

/**
 * Gráfico de área com zonas de frequência cardíaca
 */
function createHeartRateChart(dadosValidos) {
    const canvas = document.getElementById('readingsChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    console.log('Criando gráfico de frequência cardíaca com zonas...');

    try {
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dadosValidos.map(function (d) { return d.timestamp; }),
                datasets: [{
                    label: 'Frequência Cardíaca (BPM)',
                    data: dadosValidos.map(function (d) { return d.valor; }),
                    borderColor: 'rgb(239, 68, 68)',
                    backgroundColor: function (context) {
                        const ctx = context.chart.ctx;
                        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
                        gradient.addColorStop(0, 'rgba(239, 68, 68, 0.4)');
                        gradient.addColorStop(0.5, 'rgba(251, 146, 60, 0.3)');
                        gradient.addColorStop(1, 'rgba(59, 130, 246, 0.2)');
                        return gradient;
                    },
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    pointBackgroundColor: function (context) {
                        const value = context.parsed.y;
                        if (value >= 160) return 'rgb(239, 68, 68)'; // Máxima - vermelho
                        if (value >= 140) return 'rgb(251, 146, 60)'; // Limite - laranja
                        if (value >= 100) return 'rgb(34, 197, 94)'; // Aeróbica - verde
                        return 'rgb(59, 130, 246)'; // Repouso - azul
                    },
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            afterLabel: function (context) {
                                const value = context.parsed.y;
                                if (value >= 160) return '🔴 Zona Máxima';
                                if (value >= 140) return '🟠 Zona Limite';
                                if (value >= 100) return '🟢 Zona Aeróbica';
                                return '🔵 Zona de Repouso';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 50,
                        grid: {
                            color: function (context) {
                                // Linhas de grade nas zonas
                                if (context.tick.value === 160 || context.tick.value === 140 || context.tick.value === 100) {
                                    return 'rgba(0, 0, 0, 0.2)';
                                }
                                return 'rgba(0, 0, 0, 0.05)';
                            }
                        },
                        ticks: {
                            callback: function (value) {
                                return value + ' BPM';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        console.log('✅ Gráfico de frequência cardíaca criado com sucesso!');

    } catch (erro) {
        console.error('❌ Erro ao criar gráfico de frequência cardíaca:', erro);
        showNoDataMessage();
    }
}

/**
 * Gráfico de barras para contador de passos com meta
 */
function createStepsChart(dadosValidos) {
    const canvas = document.getElementById('readingsChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    console.log('Criando gráfico de passos...');

    const META_PASSOS = 10000; // Meta padrão de passos diários

    try {
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dadosValidos.map(function (d) { return d.timestamp; }),
                datasets: [{
                    label: 'Passos',
                    data: dadosValidos.map(function (d) { return d.valor; }),
                    backgroundColor: function (context) {
                        const value = context.parsed.y;
                        return value >= META_PASSOS ?
                            'rgba(34, 197, 94, 0.7)' :  // Verde se atingiu meta
                            'rgba(99, 102, 241, 0.7)';   // Roxo se não atingiu
                    },
                    borderColor: function (context) {
                        const value = context.parsed.y;
                        return value >= META_PASSOS ?
                            'rgb(34, 197, 94)' :
                            'rgb(99, 102, 241)';
                    },
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            afterLabel: function (context) {
                                const value = context.parsed.y;
                                if (value >= META_PASSOS) {
                                    const excesso = value - META_PASSOS;
                                    return '✅ Meta atingida! (+' + excesso + ' passos)';
                                } else {
                                    const faltam = META_PASSOS - value;
                                    return '⚠️ Faltam ' + faltam + ' passos para a meta';
                                }
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: function (context) {
                                // Linha de grade na meta
                                if (context.tick.value === META_PASSOS) {
                                    return 'rgba(34, 197, 94, 0.5)';
                                }
                                return 'rgba(0, 0, 0, 0.05)';
                            },
                            lineWidth: function (context) {
                                return context.tick.value === META_PASSOS ? 2 : 1;
                            }
                        },
                        ticks: {
                            callback: function (value) {
                                if (value === META_PASSOS) {
                                    return value + ' (Meta)';
                                }
                                return value;
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        console.log('✅ Gráfico de passos criado com sucesso!');

    } catch (erro) {
        console.error('❌ Erro ao criar gráfico de passos:', erro);
        showNoDataMessage();
    }
}

/**
 * Gráfico de barras para contador de repetições
 */
function createRepsChart(dadosValidos) {
    const canvas = document.getElementById('readingsChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    console.log('Criando gráfico de repetições...');

    try {
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dadosValidos.map(function (d) { return d.timestamp; }),
                datasets: [{
                    label: 'Repetições',
                    data: dadosValidos.map(function (d) { return d.valor; }),
                    backgroundColor: [
                        'rgba(139, 92, 246, 0.7)',
                        'rgba(99, 102, 241, 0.7)',
                        'rgba(59, 130, 246, 0.7)',
                        'rgba(34, 197, 94, 0.7)',
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(245, 158, 11, 0.7)'
                    ],
                    borderColor: [
                        'rgb(139, 92, 246)',
                        'rgb(99, 102, 241)',
                        'rgb(59, 130, 246)',
                        'rgb(34, 197, 94)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)'
                    ],
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        enabled: true,
                        callbacks: {
                            label: function (context) {
                                return 'Repetições: ' + context.parsed.y;
                            },
                            afterLabel: function (context) {
                                const total = context.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                                const percent = ((context.parsed.y / total) * 100).toFixed(1);
                                return percent + '% do total';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function (value) {
                                return value + ' reps';
                            },
                            stepSize: 5
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

        console.log('✅ Gráfico de repetições criado com sucesso!');

    } catch (erro) {
        console.error('❌ Erro ao criar gráfico de repetições:', erro);
        showNoDataMessage();
    }
}

/**
 * Exibe mensagem de "sem dados" e oculta o gráfico
 */
function showNoDataMessage() {
    const chartContainer = document.querySelector('.chart-container');
    const noDataMessage = document.getElementById('noChartData');

    if (chartContainer) {
        chartContainer.style.display = 'none';
    }

    if (noDataMessage) {
        noDataMessage.style.display = 'block';
    }
}

// Executar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', initDeviceChart);
