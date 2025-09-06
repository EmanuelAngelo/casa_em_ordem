<template>
  <v-card>
    <v-card-title class="text-h5">
      {{ local.id ? "Editar Lançamento" : "Novo Lançamento" }}
    </v-card-title>

    <v-card-text>
      <v-form @submit.prevent="emitSave" :disabled="saving">
        <v-row dense>
          <!-- CATEGORIA (grupo) -->
          <v-col cols="12" md="6">
            <v-select
              v-model="local.categoria_id"
              :items="categorias"
              item-title="nome"
              item-value="id"
              label="Categoria (grupo)"
              prepend-inner-icon="mdi-folder-outline"
              clearable
              @update:modelValue="onCategoriaChange"
              required
            />
          </v-col>

          <!-- SUBCATEGORIA (filtrada pela categoria) -->
          <v-col cols="12" md="6">
            <v-select
              v-model="local.subcategoria_id"
              :items="subcategoriasFiltradas"
              item-title="nome"
              item-value="id"
              label="Subcategoria"
              prepend-inner-icon="mdi-shape-outline"
              :disabled="!local.categoria_id"
              required
            />
          </v-col>

          <!-- ESCopo -->
          <v-col cols="12" md="6">
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

          <!-- Valor -->
          <v-col cols="12" md="6">
            <v-text-field
              v-model="local.valor_total"
              label="Valor total"
              type="number"
              step="0.01"
              prepend-inner-icon="mdi-currency-brl"
              required
            />
          </v-col>

          <!-- Descrição -->
          <v-col cols="12" md="8">
            <v-text-field
              v-model="local.descricao"
              label="Descrição"
              prepend-inner-icon="mdi-text"
            />
          </v-col>

          <!-- Status -->
          <v-col cols="12" md="4">
            <v-select
              v-model="local.status"
              :items="statusOptions"
              item-title="label"
              item-value="value"
              label="Status"
              prepend-inner-icon="mdi-flag"
              required
            />
          </v-col>

          <!-- Competência (DatePicker) -->
          <v-col cols="12" md="6">
            <v-text-field
              :model-value="formatBr(local.competencia)"
              label="Competência"
              hint="Mês a que a despesa se refere"
              persistent-hint
              prepend-inner-icon="mdi-calendar"
              readonly
              @click="menus.competencia = true"
            >
              <template #append-inner>
                <v-menu
                  v-model="menus.competencia"
                  :close-on-content-click="false"
                  transition="scale-transition"
                  offset-y
                >
                  <template #activator="{ props }">
                    <v-btn v-bind="props" icon>
                      <v-icon>mdi-calendar</v-icon>
                    </v-btn>
                  </template>
                  <!-- usamos v-date-picker em modo de dia (padrão) e gravamos como ISO -->
                  <v-date-picker
                    v-model="local.competencia"
                    locale="pt-BR"
                    @update:modelValue="menus.competencia = false"
                  />
                </v-menu>
              </template>
            </v-text-field>
          </v-col>

          <!-- Vencimento (DatePicker) -->
          <v-col cols="12" md="6">
            <v-text-field
              :model-value="formatBr(local.data_vencimento)"
              label="Vencimento"
              prepend-inner-icon="mdi-calendar-alert"
              readonly
              @click="menus.vencimento = true"
              required
            >
              <template #append-inner>
                <v-menu
                  v-model="menus.vencimento"
                  :close-on-content-click="false"
                  transition="scale-transition"
                  offset-y
                >
                  <template #activator="{ props }">
                    <v-btn v-bind="props" icon>
                      <v-icon>mdi-calendar</v-icon>
                    </v-btn>
                  </template>
                  <v-date-picker
                    v-model="local.data_vencimento"
                    locale="pt-BR"
                    @update:modelValue="menus.vencimento = false"
                  />
                </v-menu>
              </template>
            </v-text-field>
          </v-col>

          <!-- Dono (pessoal) -->
          <v-col cols="12" md="6" v-if="local.escopo === 'PESS'">
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

          <!-- Pagador -->
          <v-col :cols="12" :md="local.escopo === 'PESS' ? 6 : 12">
            <v-select
              v-model="local.pagador_id"
              :items="membros"
              item-title="label"
              item-value="value"
              label="Pagador"
              prepend-inner-icon="mdi-account-cash"
              required
            />
          </v-col>

          <!-- Data de pagamento (só quando PAGO) -->
          <v-col cols="12" md="6" v-if="local.status === 'PAGO'">
            <v-text-field
              :model-value="formatBr(local.data_pagamento)"
              label="Data de pagamento"
              prepend-inner-icon="mdi-calendar-check"
              readonly
              @click="menus.pagamento = true"
            >
              <template #append-inner>
                <v-menu
                  v-model="menus.pagamento"
                  :close-on-content-click="false"
                  transition="scale-transition"
                  offset-y
                >
                  <template #activator="{ props }">
                    <v-btn v-bind="props" icon>
                      <v-icon>mdi-calendar</v-icon>
                    </v-btn>
                  </template>
                  <v-date-picker
                    v-model="local.data_pagamento"
                    locale="pt-BR"
                    @update:modelValue="menus.pagamento = false"
                  />
                </v-menu>
              </template>
            </v-text-field>
          </v-col>
        </v-row>
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
import { reactive, watch, computed } from "vue";

const props = defineProps({
  model: { type: Object, default: () => ({}) },
  categorias: { type: Array, default: () => [] }, // [{id, nome}]
  subcategorias: { type: Array, default: () => [] }, // [{id, nome, categoria:{id,...}}] ou {categoria_id}
  membros: { type: Array, default: () => [] }, // [{label, value}]
  statusOptions: { type: Array, default: () => [] }, // [{label, value}]
  escopoOptions: { type: Array, default: () => [] }, // [{label, value}]
  saving: { type: Boolean, default: false },
});

const emit = defineEmits(["save", "close"]);

const local = reactive({
  id: null,
  categoria_id: null, // UI
  subcategoria_id: null, // enviado ao backend
  escopo: "COMP",
  descricao: "",
  valor_total: "",
  competencia: "", // ISO yyyy-mm-dd
  data_vencimento: "", // ISO yyyy-mm-dd
  pagador_id: null,
  status: "PENDENTE",
  data_pagamento: "", // ISO yyyy-mm-dd
  dono_pessoal_id: null,
});

const menus = reactive({
  competencia: false,
  vencimento: false,
  pagamento: false,
});

/** Normaliza subcategorias para garantir categoria_id acessível */
const subcategoriasNormalizadas = computed(() =>
  (props.subcategorias || []).map((s) => ({
    ...s,
    categoria_id: s.categoria_id ?? s.categoria?.id ?? null,
  }))
);

/** Filtra subcategorias conforme categoria escolhida */
const subcategoriasFiltradas = computed(() => {
  if (!local.categoria_id) return [];
  return subcategoriasNormalizadas.value.filter(
    (s) => s.categoria_id === local.categoria_id
  );
});

/** Preenche o formulário ao abrir/editar */
watch(
  () => props.model,
  (m) => {
    Object.assign(local, {
      id: m?.id ?? null,
      // tenta usar campo direto; se não tiver, usa aninhado
      categoria_id: m?.categoria_id ?? m?.categoria?.id ?? null,
      subcategoria_id: m?.subcategoria_id ?? m?.subcategoria?.id ?? null,
      escopo: m?.escopo ?? "COMP",
      descricao: m?.descricao ?? "",
      valor_total: m?.valor_total ?? "",
      competencia: m?.competencia ?? "",
      data_vencimento: m?.data_vencimento ?? "",
      pagador_id: m?.pagador_id ?? m?.pagador?.id ?? null,
      status: m?.status ?? "PENDENTE",
      data_pagamento: m?.data_pagamento ?? "",
      dono_pessoal_id: m?.dono_pessoal_id ?? m?.dono_pessoal?.id ?? null,
    });

    // se tem subcategoria definida, garante que categoria_id acompanha
    if (!local.categoria_id && local.subcategoria_id) {
      const sub = subcategoriasNormalizadas.value.find(
        (s) => s.id === local.subcategoria_id
      );
      local.categoria_id = sub?.categoria_id ?? null;
    }
  },
  { immediate: true, deep: true }
);

/** Ao trocar a categoria, invalida subcategoria fora do grupo */
function onCategoriaChange() {
  const match = subcategoriasNormalizadas.value.find(
    (s) => s.id === local.subcategoria_id
  );
  if (!match || match.categoria_id !== local.categoria_id) {
    local.subcategoria_id = null;
  }
}

/** Se status deixar de ser PAGO, limpa data_pagamento (evita enviar lixo) */
watch(
  () => local.status,
  (st) => {
    if (st !== "PAGO") {
      local.data_pagamento = "";
    }
  }
);

/** Se escopo virar COMP, limpa dono_pessoal_id (regra do backend) */
watch(
  () => local.escopo,
  (esc) => {
    if (esc === "COMP") {
      local.dono_pessoal_id = null;
    }
  }
);

// 👇 cole isso junto das outras funções
function toIsoDate(value) {
  if (!value) return value;
  if (typeof value === "string") {
    // já está em string; confia que vem "YYYY-MM-DD"
    return value;
  }
  // Date -> "YYYY-MM-DD"
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** Formata ISO -> dd/mm/yyyy para exibição */
function formatBr(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("pt-BR", { timeZone: "UTC" });
}

/** Emite payload limpo para o backend */
function emitSave() {
  const payload = { ...local };

  // backend não precisa receber categoria_id (somente subcategoria_id)
  delete payload.categoria_id;

  // 🔧 Normaliza datas para "YYYY-MM-DD"
  payload.competencia = toIsoDate(payload.competencia);
  payload.data_vencimento = toIsoDate(payload.data_vencimento);
  if (payload.data_pagamento) {
    payload.data_pagamento = toIsoDate(payload.data_pagamento);
  }

  // 🔒 Regras: se escopo COMP, não enviar dono_pessoal_id
  if (payload.escopo === "COMP") {
    delete payload.dono_pessoal_id;
  }

  // limpa vazios/nulos
  Object.keys(payload).forEach((k) => {
    if (payload[k] === "" || payload[k] === null) delete payload[k];
  });

  // ✅ garantias mínimas (evita 400 “field required”)
  if (!payload.subcategoria_id) {
    // mantém seu comportamento de salvar via pai: quem mostra o erro é o pai
    // mas podemos prevenir com um early return, se preferir:
    // return;
  }
  if (!payload.pagador_id) {
    // idem
  }

  emit("save", payload);
}
</script>
