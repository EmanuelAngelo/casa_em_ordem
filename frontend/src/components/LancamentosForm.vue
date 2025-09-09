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

          <!-- Escopo -->
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

          <!-- Competência (NÃO alteramos ao ligar cartão) -->
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
                  <v-date-picker
                    v-model="local.competencia"
                    locale="pt-BR"
                    @update:modelValue="menus.competencia = false"
                  />
                </v-menu>
              </template>
            </v-text-field>
          </v-col>

          <!-- Vencimento -->
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

          <!-- =================== COMPRA NO CARTÃO =================== -->
          <v-col cols="12" md="6">
            <v-switch
              v-model="local.usar_cartao"
              inset
              color="blue-darken-3"
              label="Compra no cartão?"
              hide-details
            />
          </v-col>

          <!-- Cartão + Novo Cartão -->
          <v-col cols="12" md="6" v-if="local.usar_cartao">
            <v-select
              v-model="local.cartao_id"
              :items="cartoesLocal"
              item-title="nome"
              item-value="id"
              label="Cartão"
              prepend-inner-icon="mdi-credit-card-outline"
              clearable
            >
              <template #append>
                <v-btn
                  size="small"
                  variant="text"
                  icon
                  @click.stop="showNewCard = !showNewCard"
                  :aria-label="
                    showNewCard ? 'Fechar novo cartão' : 'Novo cartão'
                  "
                >
                  <v-icon>{{ showNewCard ? "mdi-close" : "mdi-plus" }}</v-icon>
                </v-btn>
              </template>
            </v-select>
          </v-col>

          <!-- Novo Cartão inline -->
          <v-col cols="12" v-if="local.usar_cartao && showNewCard">
            <v-card variant="tonal" class="pa-3">
              <v-row dense>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="newCardName"
                    label="Nome do cartão"
                    prepend-inner-icon="mdi-credit-card-plus-outline"
                    :disabled="creatingCard"
                    autofocus
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="newCardDueDay"
                    label="Dia de vencimento (1–31)"
                    type="number"
                    min="1"
                    max="31"
                    prepend-inner-icon="mdi-calendar-alert"
                    :disabled="creatingCard"
                    required
                  />
                </v-col>

                <v-col cols="12" class="d-flex justify-end">
                  <v-btn
                    variant="text"
                    class="me-2"
                    :disabled="creatingCard"
                    @click="cancelNewCard"
                  >
                    Cancelar
                  </v-btn>
                  <v-btn
                    color="blue-darken-3"
                    :loading="creatingCard"
                    :disabled="!newCardName || !validNewCardDueDay"
                    @click="createCard"
                  >
                    Salvar cartão
                  </v-btn>
                </v-col>
              </v-row>
            </v-card>
          </v-col>

          <!-- Parcelas (mostra apenas quando é compra no cartão) -->
          <v-col cols="12" md="4" v-if="local.usar_cartao">
            <v-text-field
              v-model.number="local.parcelas_total"
              label="Total de parcelas"
              type="number"
              min="1"
              prepend-inner-icon="mdi-format-list-numbered"
              required
            />
          </v-col>

          <v-col cols="12" md="4" v-if="local.usar_cartao">
            <v-text-field
              v-model.number="local.parcela_numero"
              label="Parcela atual"
              type="number"
              min="1"
              :max="local.parcelas_total || 1"
              prepend-inner-icon="mdi-numeric"
              required
            />
          </v-col>

          <v-col cols="12" md="4" v-if="local.usar_cartao">
            <v-text-field
              :model-value="
                cartaoSelecionado
                  ? `Fecha dia ${cartaoSelecionado.dia_vencimento}`
                  : '—'
              "
              label="Vencimento do cartão"
              prepend-inner-icon="mdi-calendar-month-outline"
              readonly
              hint="Define a data de vencimento com base no cartão"
              persistent-hint
            />
          </v-col>
          <!-- ================= /COMPRA NO CARTÃO =================== -->

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
import { reactive, ref, watch, computed } from "vue";
import axios from "@/api/axios";

const props = defineProps({
  model: { type: Object, default: () => ({}) },
  categorias: { type: Array, default: () => [] }, // [{id, nome}]
  subcategorias: { type: Array, default: () => [] }, // [{id, nome, categoria:{id,...}}] ou {categoria_id}
  membros: { type: Array, default: () => [] }, // [{label, value}]
  statusOptions: { type: Array, default: () => [] }, // [{label, value}]
  escopoOptions: { type: Array, default: () => [] }, // [{label, value}]
  cartoes: { type: Array, default: () => [] }, // [{id, nome, dia_vencimento}]
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
  competencia: "", // ISO yyyy-mm-dd (NÃO alteramos quando ligar cartão)
  data_vencimento: "", // ISO yyyy-mm-dd (autopreenche ao escolher cartão)
  pagador_id: null,
  status: "PENDENTE",
  data_pagamento: "", // ISO yyyy-mm-dd
  dono_pessoal_id: null,
  usar_cartao: false,
  cartao_id: null,
  parcelas_total: 1,
  parcela_numero: 1,
});

const menus = reactive({
  competencia: false,
  vencimento: false,
  pagamento: false,
});

/* ====== Cartões (inline create) ====== */
const cartoesLocal = ref([]);
const showNewCard = ref(false);
const newCardName = ref("");
const newCardDueDay = ref(null); // 1..31
const creatingCard = ref(false);

const validNewCardDueDay = computed(() => {
  const n = Number(newCardDueDay.value);
  return Number.isInteger(n) && n >= 1 && n <= 31;
});

watch(
  () => props.cartoes,
  (arr) => {
    cartoesLocal.value = Array.isArray(arr) ? [...arr] : [];
  },
  { immediate: true }
);

function cancelNewCard() {
  showNewCard.value = false;
  newCardName.value = "";
  newCardDueDay.value = null;
}

async function createCard() {
  if (!newCardName.value || !validNewCardDueDay.value) return;
  creatingCard.value = true;
  try {
    // ajuste os campos conforme o seu backend de cartões
    const { data } = await axios.post("/cartoes/", {
      nome: newCardName.value,
      dia_vencimento: newCardDueDay.value,
    });
    cartoesLocal.value.push(data);
    local.cartao_id = data.id; // seleciona o novo cartão
    applyCardDueDate(); // autopreenche vencimento
    cancelNewCard();
  } catch (e) {
    console.error("Erro ao criar cartão:", e);
  } finally {
    creatingCard.value = false;
  }
}
/* ===================================== */

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

/** Cartão selecionado (obj) */
const cartaoSelecionado = computed(
  () => cartoesLocal.value.find((c) => c.id === local.cartao_id) || null
);

/** Preenche o formulário ao abrir/editar */
watch(
  () => props.model,
  (m) => {
    Object.assign(local, {
      id: m?.id ?? null,
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
      usar_cartao: !!(m?.cartao_id ?? m?.cartao?.id),
      cartao_id: m?.cartao_id ?? m?.cartao?.id ?? null,
      parcelas_total: m?.parcelas_total ?? 1,
      parcela_numero: m?.parcela_numero ?? 1,
    });

    // garante categoria_id pela subcategoria, se necessário
    if (!local.categoria_id && local.subcategoria_id) {
      const sub = subcategoriasNormalizadas.value.find(
        (s) => s.id === local.subcategoria_id
      );
      local.categoria_id = sub?.categoria_id ?? null;
    }

    // Se já vier com cartão, podemos sugerir vencimento se não houver
    if (local.usar_cartao && !local.data_vencimento) {
      applyCardDueDate();
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

/** Se status deixar de ser PAGO, limpa data_pagamento */
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

/** Se desmarcar "Compra no cartão", limpa dados relacionados */
watch(
  () => local.usar_cartao,
  (on) => {
    if (!on) {
      local.cartao_id = null;
      local.parcelas_total = 1;
      local.parcela_numero = 1;
      showNewCard.value = false;
      newCardName.value = "";
      newCardDueDay.value = null;
      // NÃO mexemos em competencia
      // Também não alteramos data_vencimento automaticamente aqui
    } else {
      // ligou: se já houver cartão selecionado, sugere vencimento
      applyCardDueDate();
    }
  }
);

/** Quando trocar o cartão, sugere data de vencimento (sem mexer na competência) */
watch(
  () => local.cartao_id,
  () => {
    applyCardDueDate();
  }
);

/** Calcula a próxima data de vencimento pelo dia do cartão, a partir de HOJE */
function nextDueDateFromToday(dueDay) {
  const today = new Date();
  const y = today.getFullYear();
  const m = today.getMonth(); // 0..11
  const thisMonthDue = new Date(Date.UTC(y, m, Math.min(dueDay, 28))); // evita overflow em meses curtos
  if (today.getUTCDate() <= dueDay) {
    return isoDate(y, m, dueDay);
  } else {
    // próximo mês
    const next = new Date(Date.UTC(y, m + 1, 1));
    return isoDate(next.getUTCFullYear(), next.getUTCMonth(), dueDay);
  }
}

/** Aplica vencimento baseado no cartão, sem tocar na competencia */
function applyCardDueDate() {
  if (!local.usar_cartao) return;
  const c = cartaoSelecionado.value;
  if (!c || !c.dia_vencimento) return;
  // Só sugere se o campo estiver vazio, para não sobrescrever edição manual
  if (!local.data_vencimento) {
    local.data_vencimento = nextDueDateFromToday(Number(c.dia_vencimento));
  }
}

/** Helpers de data */
function isoDate(year, monthZeroBased, day) {
  const pad = (n) => String(n).padStart(2, "0");
  return `${year}-${pad(monthZeroBased + 1)}-${pad(Math.min(day, 28))}`;
}

function toIsoDate(value) {
  if (!value) return value;
  if (typeof value === "string") {
    return value; // assume "YYYY-MM-DD"
  }
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** ISO -> dd/mm/yyyy */
function formatBr(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString("pt-BR", { timeZone: "UTC" });
}

/** Emite payload limpo para o backend */
function emitSave() {
  const payload = { ...local };

  // backend não precisa receber categoria_id
  delete payload.categoria_id;

  // se não for compra no cartão, remover campos de cartão do payload
  if (!payload.usar_cartao) {
    delete payload.cartao_id;
    delete payload.parcelas_total;
    delete payload.parcela_numero;
  }
  delete payload.usar_cartao;

  // normaliza datas
  payload.competencia = toIsoDate(payload.competencia);
  payload.data_vencimento = toIsoDate(payload.data_vencimento);
  if (payload.data_pagamento) {
    payload.data_pagamento = toIsoDate(payload.data_pagamento);
  }

  // regra: se COMP, não envia dono_pessoal_id
  if (payload.escopo === "COMP") {
    delete payload.dono_pessoal_id;
  }

  // remove vazios/nulos
  Object.keys(payload).forEach((k) => {
    if (payload[k] === "" || payload[k] === null) delete payload[k];
  });

  emit("save", payload);
}
</script>
