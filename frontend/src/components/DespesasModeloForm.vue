<template>
  <v-card>
    <v-card-title class="text-h5">
      {{ local.id ? "Editar Modelo" : "Novo Modelo" }}
    </v-card-title>

    <v-card-text>
      <v-form @submit.prevent="emitSave" :disabled="saving">
        <v-row dense>
          <v-col cols="12" md="8">
            <v-text-field
              v-model="local.nome"
              label="Nome"
              prepend-inner-icon="mdi-text"
              required
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-select
              v-model="local.categoria_id"
              :items="categorias"
              item-title="nome"
              item-value="id"
              label="Categoria"
              prepend-inner-icon="mdi-folder-outline"
              clearable
              required
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-select
              v-model="local.escopo"
              :items="escopoOptions"
              item-title="label"
              item-value="value"
              label="Escopo"
              prepend-inner-icon="mdi-account-multiple-outline"
              required
            />
          </v-col>

          <v-col cols="12" md="4" v-if="local.escopo === 'PESS'">
            <v-select
              v-model="local.dono_pessoal_id"
              :items="membros"
              item-title="label"
              item-value="value"
              label="Dono (pessoal)"
              prepend-inner-icon="mdi-account"
              required
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model="local.valor_previsto"
              label="Valor Previsto"
              type="number"
              step="0.01"
              prepend-inner-icon="mdi-currency-brl"
              required
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-text-field
              v-model.number="local.dia_vencimento"
              label="Dia de Vencimento"
              type="number"
              min="1"
              max="28"
              prepend-inner-icon="mdi-calendar-alert"
              required
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-select
              v-model="local.periodicidade"
              :items="periodicidadeOptions"
              item-title="label"
              item-value="value"
              label="Periodicidade"
              prepend-inner-icon="mdi-calendar"
              required
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-select
              v-model="local.recorrente"
              :items="recorrenteOptions"
              item-title="label"
              item-value="value"
              label="Recorrente?"
              prepend-inner-icon="mdi-repeat"
              required
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-select
              v-model="local.regra_rateio"
              :items="regraRateioOptions"
              item-title="label"
              item-value="value"
              label="Regra de Rateio"
              prepend-inner-icon="mdi-scale-balance"
              :disabled="local.escopo === 'PESS'"
              hint="Para Pessoal, sempre 'IGUAL' (100% do dono)"
              persistent-hint
              required
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-select
              v-model="local.ativo"
              :items="ativoOptions"
              item-title="label"
              item-value="value"
              label="Status"
              prepend-inner-icon="mdi-toggle-switch"
              required
            />
          </v-col>
        </v-row>

        <!-- Bloco Rateio Padrão (apenas COMP) -->
        <v-divider class="my-4" />
        <v-alert
          v-if="local.escopo === 'PESS'"
          type="info"
          variant="tonal"
          class="mb-2"
        >
          Modelos pessoais não utilizam rateio (100% do dono).
        </v-alert>

        <div v-if="local.escopo === 'COMP'">
          <div class="d-flex align-center mb-2">
            <h3 class="text-subtitle-1 mb-0">Rateio Padrão</h3>
            <v-spacer />
            <v-btn
              size="small"
              prepend-icon="mdi-plus"
              @click="addRateio"
              :disabled="local.regra_rateio === 'IGUAL'"
            >
              Adicionar Linha
            </v-btn>
          </div>

          <v-table density="compact">
            <thead>
              <tr>
                <th>Membro</th>
                <th v-if="local.regra_rateio === 'PERCENTUAL'">
                  Percentual (%)
                </th>
                <th v-if="local.regra_rateio === 'VALOR_FIXO'">
                  Valor Fixo (R$)
                </th>
                <th style="width: 56px"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(r, idx) in local.rateios"
                :key="r.__key || r.id || idx"
              >
                <td style="min-width: 220px">
                  <v-select
                    v-model="r.membro_id"
                    :items="membros"
                    item-title="label"
                    item-value="value"
                    density="compact"
                    hide-details
                    clearable
                  />
                </td>

                <td v-if="local.regra_rateio === 'PERCENTUAL'">
                  <v-text-field
                    v-model.number="r.percentual"
                    type="number"
                    min="0"
                    max="100"
                    step="0.01"
                    density="compact"
                    hide-details
                  />
                </td>

                <td v-if="local.regra_rateio === 'VALOR_FIXO'">
                  <v-text-field
                    v-model.number="r.valor_fixo"
                    type="number"
                    min="0"
                    step="0.01"
                    density="compact"
                    hide-details
                  />
                </td>

                <td class="text-right">
                  <v-btn
                    icon
                    size="small"
                    variant="text"
                    @click="removeRateio(idx)"
                    :disabled="local.regra_rateio === 'IGUAL'"
                  >
                    <v-icon color="red">mdi-delete</v-icon>
                  </v-btn>
                </td>
              </tr>

              <tr v-if="local.regra_rateio === 'IGUAL'">
                <td colspan="4">
                  Rateio igualitário: o sistema dividirá automaticamente entre
                  os membros do casal.
                </td>
              </tr>
            </tbody>
          </v-table>
        </div>
      </v-form>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn variant="text" @click="$emit('close')">Cancelar</v-btn>
      <v-btn color="blue-darken-3" :loading="saving" @click="emitSave">
        Salvar
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { reactive, watch } from "vue";

const props = defineProps({
  model: { type: Object, default: () => ({}) },
  categorias: { type: Array, default: () => [] }, // [{id, nome}]
  membros: { type: Array, default: () => [] }, // [{label, value}]
  saving: { type: Boolean, default: false },
});
const emit = defineEmits(["save", "close"]);

const escopoOptions = [
  { label: "Compartilhada", value: "COMP" },
  { label: "Pessoal", value: "PESS" },
];
const periodicidadeOptions = [
  { label: "Mensal", value: "MENSAL" },
  { label: "Anual", value: "ANUAL" },
  { label: "Única", value: "UNICA" },
];
const regraRateioOptions = [
  { label: "Igual para todos", value: "IGUAL" },
  { label: "Por percentual", value: "PERCENTUAL" },
  { label: "Por valor fixo", value: "VALOR_FIXO" },
];
const recorrenteOptions = [
  { label: "Sim", value: true },
  { label: "Não", value: false },
];
const ativoOptions = [
  { label: "Ativo", value: true },
  { label: "Inativo", value: false },
];

const local = reactive({
  id: null,
  nome: "",
  categoria_id: null,
  escopo: "COMP",
  dono_pessoal_id: null,
  valor_previsto: "",
  dia_vencimento: 1,
  recorrente: true,
  periodicidade: "MENSAL",
  regra_rateio: "IGUAL",
  ativo: true,
  rateios: [], // [{id?, membro_id, percentual?, valor_fixo?}]
});

watch(
  () => props.model,
  (m) => {
    Object.assign(local, {
      id: m?.id ?? null,
      nome: m?.nome ?? "",
      categoria_id: m?.categoria_id ?? m?.categoria?.id ?? null,
      escopo: m?.escopo ?? "COMP",
      dono_pessoal_id: m?.dono_pessoal_id ?? m?.dono_pessoal?.id ?? null,
      valor_previsto: m?.valor_previsto ?? "",
      dia_vencimento: m?.dia_vencimento ?? 1,
      recorrente: m?.recorrente ?? true,
      periodicidade: m?.periodicidade ?? "MENSAL",
      regra_rateio: m?.regra_rateio ?? "IGUAL",
      ativo: m?.ativo ?? true,
      rateios: Array.isArray(m?.rateios)
        ? m.rateios.map((r, i) => ({ __key: `r-${i}-${r.id || ""}`, ...r }))
        : [],
    });
    // regra de segurança: se escopo = PESS, força IGUAL e limpa rateios
    if (local.escopo === "PESS") {
      local.regra_rateio = "IGUAL";
      local.rateios = [];
    }
  },
  { immediate: true, deep: true }
);

// quando mudar escopo ou regra, ajusta linhas
watch(
  () => local.escopo,
  (v) => {
    if (v === "PESS") {
      local.regra_rateio = "IGUAL";
      local.rateios = [];
    }
  }
);

watch(
  () => local.regra_rateio,
  (v) => {
    if (v === "IGUAL") {
      local.rateios = [];
    } else {
      // mantém linhas existentes, mas zera campos incompatíveis
      local.rateios = (local.rateios || []).map((r, i) => ({
        __key: r.__key || `r-${i}-${r.id || ""}`,
        membro_id: r.membro_id ?? null,
        percentual: v === "PERCENTUAL" ? r.percentual ?? null : null,
        valor_fixo: v === "VALOR_FIXO" ? r.valor_fixo ?? null : null,
        id: r.id,
      }));
    }
  }
);

function addRateio() {
  if (local.regra_rateio === "IGUAL") return;
  local.rateios.push({
    __key: `r-${Date.now()}-${Math.random()}`,
    membro_id: null,
    percentual: local.regra_rateio === "PERCENTUAL" ? 0 : null,
    valor_fixo: local.regra_rateio === "VALOR_FIXO" ? 0 : null,
  });
}

function removeRateio(idx) {
  local.rateios.splice(idx, 1);
}

function emitSave() {
  const payload = { ...local };

  // regras de consistência
  if (payload.escopo === "PESS") {
    payload.regra_rateio = "IGUAL";
    payload.rateios = [];
  }
  if (payload.regra_rateio === "IGUAL") {
    payload.rateios = [];
  }
  // limpa campos vazios
  Object.keys(payload).forEach((k) => {
    if (payload[k] === "" || payload[k] === null) delete payload[k];
  });

  emit("save", payload);
}
</script>
