<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Relatório Financeiro</v-toolbar-title>
      </v-toolbar>

      <v-card-text>
        <!-- Filtros -->
        <v-row>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="competencia"
              label="Competência"
              type="month"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="membroFiltro"
              :items="membrosOptions"
              item-title="label"
              item-value="value"
              label="Visão"
            />
          </v-col>
        </v-row>

        <v-divider class="my-4"></v-divider>

        <!-- Resultados -->
        <v-skeleton-loader
          v-if="loading"
          type="card, list-item-three-line@3"
        ></v-skeleton-loader>
        <div v-else-if="!relatorioData">
          <v-alert type="info" variant="tonal"
            >Selecione uma competência para ver o relatório.</v-alert
          >
        </div>
        <div v-else>
          <v-row>
            <!-- Card de Resumo -->
            <v-col cols="12" md="4">
              <v-card variant="tonal">
                <v-card-text>
                  <div class="text-caption">Salário Declarado</div>
                  <div class="text-h4 font-weight-bold">
                    {{ formatCurrency(relatorioData.salario_declarado) }}
                  </div>
                  <v-divider class="my-2"></v-divider>
                  <div class="text-caption">Total Gasto</div>
                  <div class="text-h5" :class="corGasto">
                    {{ formatCurrency(relatorioData.total_gasto) }}
                  </div>
                  <v-progress-linear
                    :model-value="porcentagemGasta"
                    :color="corGasto"
                    height="20"
                    class="mt-3"
                    rounded
                  >
                    <template #default="{ value }">
                      <strong>{{ Math.ceil(value) }}%</strong>
                    </template>
                  </v-progress-linear>
                  <div class="text-caption mt-3">Saldo Restante</div>
                  <div class="text-h6" :class="corSaldo">
                    {{
                      formatCurrency(
                        relatorioData.salario_declarado -
                          relatorioData.total_gasto
                      )
                    }}
                  </div>
                </v-card-text>
              </v-card>
            </v-col>

            <!-- Card de Gastos por Categoria -->
            <v-col cols="12" md="8">
              <v-card variant="tonal">
                <v-card-title>Gastos por Categoria</v-card-title>
                <v-card-text>
                  <v-list
                    lines="two"
                    v-if="relatorioData.gastos_por_categoria.length"
                  >
                    <v-list-item
                      v-for="gasto in relatorioData.gastos_por_categoria"
                      :key="gasto.lancamento__subcategoria__categoria__nome"
                    >
                      <v-list-item-title>{{
                        gasto.lancamento__subcategoria__categoria__nome
                      }}</v-list-item-title>
                      <v-list-item-subtitle>{{
                        formatCurrency(gasto.valor_total)
                      }}</v-list-item-subtitle>
                      <template #append>
                        <v-chip size="small" label
                          >{{
                            (
                              (gasto.valor_total / relatorioData.total_gasto) *
                              100
                            ).toFixed(1)
                          }}%</v-chip
                        >
                      </template>
                    </v-list-item>
                  </v-list>
                  <div v-else class="text-center text-grey">
                    Nenhum gasto encontrado para esta competência.
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </div>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, watch, onMounted, computed } from "vue";
import axios from "@/api/axios";

const loading = ref(false);
const competencia = ref(new Date().toISOString().slice(0, 7)); // "YYYY-MM"
const membroFiltro = ref("geral");
const membrosOptions = ref([{ label: "Visão do Grupo", value: "geral" }]);
const relatorioData = ref(null);

onMounted(async () => {
  await fetchMembros();
  if (competencia.value && membroFiltro.value) {
    fetchRelatorio();
  }
});

watch([competencia, membroFiltro], () => {
  fetchRelatorio();
});

async function fetchMembros() {
  try {
    // >>> ALTERADO: /casais/meu/ -> /grupos/meu/
    const { data } = await axios.get("/grupos/meu/");
    const membros = (data?.membros || []).map((m) => ({
      label: `Visão de ${m.usuario.first_name || m.usuario.username}`,
      value: m.usuario.id,
    }));
    membrosOptions.value.push(...membros);
  } catch (e) {
    console.error("Erro ao carregar membros para o filtro.");
  }
}

async function fetchRelatorio() {
  if (!competencia.value) {
    relatorioData.value = null;
    return;
  }
  loading.value = true;
  relatorioData.value = null;
  try {
    const { data } = await axios.get("/relatorio-financeiro/", {
      params: {
        competencia: competencia.value,
        membro_id: membroFiltro.value,
      },
    });
    relatorioData.value = data;
  } catch (error) {
    console.error("Erro ao buscar relatório:", error);
  } finally {
    loading.value = false;
  }
}

const porcentagemGasta = computed(() => {
  if (!relatorioData.value || !relatorioData.value.salario_declarado) return 0;
  return (
    (relatorioData.value.total_gasto / relatorioData.value.salario_declarado) *
    100
  );
});

const corGasto = computed(() => {
  const p = porcentagemGasta.value;
  if (p > 90) return "red";
  if (p > 70) return "orange";
  return "blue";
});

const corSaldo = computed(() => {
  if (!relatorioData.value) return "";
  return relatorioData.value.salario_declarado -
    relatorioData.value.total_gasto <
    0
    ? "red-darken-2"
    : "green-darken-2";
});

function formatCurrency(value) {
  return Number(value || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}
</script>
