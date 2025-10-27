<template>
  <v-card>
    <v-card-title class="text-h5">
      {{ local.id ? "Editar Lançamento" : "Novo Lançamento" }}
    </v-card-title>

    <v-card-text class="pt-4">
      <v-form @submit.prevent="emitSave" :disabled="saving">
        <v-row dense>
          <!-- Forma de Pagamento -->
          <v-col cols="12">
            <label class="v-label mb-1">Forma de Pagamento</label>
            <v-btn-toggle
              v-model="local.paymentMethod"
              color="blue-darken-3"
              variant="outlined"
              divided
              class="w-100"
              :disabled="!!local.id"
            >
              <v-btn value="cash" class="flex-grow-1">
                <v-icon start>mdi-cash</v-icon>
                Pix / Cédula / Débito
              </v-btn>
              <v-btn value="card" class="flex-grow-1">
                <v-icon start>mdi-credit-card</v-icon>
                Cartão de Crédito
              </v-btn>
            </v-btn-toggle>
            <div v-if="local.id" class="text-caption text-disabled mt-1">
              Não é possível alterar a forma de pagamento de um lançamento
              existente.
            </div>
          </v-col>

          <!-- Campos Comuns -->
          <v-col cols="12">
            <v-text-field
              v-model="local.descricao"
              label="Descrição da Despesa"
              prepend-inner-icon="mdi-text"
              variant="outlined"
              density="compact"
              required
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="local.valor_total"
              label="Valor Total"
              type="number"
              step="0.01"
              prefix="R$"
              prepend-inner-icon="mdi-currency-brl"
              variant="outlined"
              density="compact"
              required
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              :model-value="formatBr(local.competencia)"
              label="Data da Despesa (Competência)"
              prepend-inner-icon="mdi-calendar"
              variant="outlined"
              density="compact"
              readonly
              @click="menus.competencia = true"
              required
            >
              <template #append-inner>
                <v-menu
                  v-model="menus.competencia"
                  :close-on-content-click="false"
                  transition="scale-transition"
                >
                  <template #activator="{ props: menuProps }">
                    <v-btn v-bind="menuProps" icon size="small" variant="text">
                      <v-icon>mdi-calendar</v-icon>
                    </v-btn>
                  </template>
                  <v-date-picker
                    v-model="local.competencia"
                    @update:modelValue="menus.competencia = false"
                    locale="pt-BR"
                  />
                </v-menu>
              </template>
            </v-text-field>
          </v-col>

          <v-col cols="12" md="6">
            <v-select
              v-model="local.categoria_id"
              :items="categorias"
              item-title="nome"
              item-value="id"
              label="Categoria"
              prepend-inner-icon="mdi-folder-outline"
              variant="outlined"
              density="compact"
              @update:modelValue="onCategoriaChange"
              required
            />
          </v-col>
          <v-col cols="12" md="6">
            <v-select
              v-model="local.subcategoria_id"
              :items="subcategoriasFiltradas"
              item-title="nome"
              item-value="id"
              label="Subcategoria"
              prepend-inner-icon="mdi-shape-outline"
              variant="outlined"
              density="compact"
              :disabled="!local.categoria_id"
              required
            />
          </v-col>

          <v-col cols="12"><v-divider class="my-2"></v-divider></v-col>

          <!-- Cartão de Crédito (apenas quando paymentMethod === 'card') -->
          <template v-if="local.paymentMethod === 'card'">
            <v-col cols="12" md="6">
              <v-select
                v-model="local.cartao_id"
                :items="cartoesLocal"
                item-title="nome"
                item-value="id"
                label="Qual cartão foi usado?"
                prepend-inner-icon="mdi-credit-card-outline"
                variant="outlined"
                density="compact"
                required
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
                    <v-icon>{{
                      showNewCard ? "mdi-close" : "mdi-plus"
                    }}</v-icon>
                  </v-btn>
                </template>
              </v-select>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model.number="local.parcelas_total"
                label="Total de Parcelas"
                type="number"
                min="1"
                prepend-inner-icon="mdi-format-list-numbered"
                variant="outlined"
                density="compact"
                required
              />
            </v-col>
            <v-col cols="12">
              <v-text-field
                :model-value="formatBr(local.data_vencimento)"
                label="Vencimento da 1ª Parcela"
                prepend-inner-icon="mdi-calendar-alert"
                variant="outlined"
                density="compact"
                readonly
                @click="menus.vencimento = true"
                required
              >
                <template #append-inner>
                  <v-menu
                    v-model="menus.vencimento"
                    :close-on-content-click="false"
                    transition="scale-transition"
                  >
                    <template #activator="{ props: menuProps }">
                      <v-btn
                        v-bind="menuProps"
                        icon
                        size="small"
                        variant="text"
                      >
                        <v-icon>mdi-calendar</v-icon>
                      </v-btn>
                    </template>
                    <v-date-picker
                      v-model="local.data_vencimento"
                      @update:modelValue="menus.vencimento = false"
                      locale="pt-BR"
                    />
                  </v-menu>
                </template>
              </v-text-field>
            </v-col>
          </template>

          <!-- Novo Cartão (toggle) -->
          <v-col cols="12" v-if="local.paymentMethod === 'card' && showNewCard">
            <v-card variant="tonal" class="pa-3">
              <v-row dense>
                <v-col cols="12"
                  ><div class="text-subtitle-1">Novo Cartão</div></v-col
                >
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="newCard.nome"
                    label="Nome do cartão (Ex: Maria - Nubank)"
                    prepend-inner-icon="mdi-credit-card-plus-outline"
                    :disabled="creatingCard"
                    autofocus
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="newCard.bandeira"
                    :items="bandeiraOptions"
                    label="Bandeira"
                    prepend-inner-icon="mdi-flag"
                    :disabled="creatingCard"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="newCard.dia_vencimento"
                    label="Dia de vencimento (1–28)"
                    type="number"
                    min="1"
                    max="28"
                    prepend-inner-icon="mdi-calendar-alert"
                    :disabled="creatingCard"
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="newCard.dia_fechamento"
                    label="Dia de fechamento (1–28)"
                    type="number"
                    min="1"
                    max="28"
                    prepend-inner-icon="mdi-calendar-lock"
                    :disabled="creatingCard"
                    required
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="newCard.limite"
                    label="Limite (opcional)"
                    type="number"
                    step="0.01"
                    prepend-inner-icon="mdi-cash-lock"
                    :disabled="creatingCard"
                  />
                </v-col>
                <v-col cols="12" class="d-flex justify-end">
                  <v-btn
                    variant="text"
                    class="me-2"
                    :disabled="creatingCard"
                    @click="cancelNewCard"
                    >Cancelar</v-btn
                  >
                  <v-btn
                    color="blue-darken-3"
                    :loading="creatingCard"
                    :disabled="
                      !newCard.nome ||
                      !newCard.dia_vencimento ||
                      !newCard.dia_fechamento
                    "
                    @click="createCard"
                  >
                    Salvar cartão
                  </v-btn>
                </v-col>
              </v-row>
            </v-card>
          </v-col>

          <!-- Detalhes -->
          <v-col cols="12" md="4">
            <v-select
              v-model="local.escopo"
              :items="escopoOptions"
              item-title="label"
              item-value="value"
              label="Escopo"
              prepend-inner-icon="mdi-account-group-outline"
              variant="outlined"
              density="compact"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="local.pagador_id"
              :items="membros"
              item-title="label"
              item-value="value"
              label="Quem Pagou?"
              prepend-inner-icon="mdi-account-cash-outline"
              variant="outlined"
              density="compact"
            />
          </v-col>
          <v-col v-if="local.escopo === 'PESS'" cols="12" md="4">
            <v-select
              v-model="local.dono_pessoal_id"
              :items="membros"
              item-title="label"
              item-value="value"
              label="Dono da Despesa"
              prepend-inner-icon="mdi-account-outline"
              variant="outlined"
              density="compact"
            />
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn variant="text" @click="$emit('close')">Cancelar</v-btn>
      <v-btn color="blue-darken-3" :loading="saving" @click="emitSave"
        >Salvar</v-btn
      >
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { reactive, ref, watch, computed } from "vue";
import axios from "@/api/axios";

const props = defineProps({
  model: { type: Object, default: () => ({}) },
  categorias: { type: Array, default: () => [] },
  subcategorias: { type: Array, default: () => [] },
  membros: { type: Array, default: () => [] },
  statusOptions: { type: Array, default: () => [] },
  escopoOptions: { type: Array, default: () => [] },
  cartoes: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
  currentUserId: { type: Number, default: null },
});

const emit = defineEmits(["save", "close"]);

const local = reactive({
  id: null,
  paymentMethod: "cash",
  descricao: "",
  valor_total: "",
  competencia: new Date(),
  data_vencimento: new Date(),
  categoria_id: null,
  subcategoria_id: null,
  cartao_id: null,
  parcelas_total: 1,
  escopo: "COMP",
  pagador_id: null,
  dono_pessoal_id: null,
  status: "PENDENTE",
});

const menus = reactive({ competencia: false, vencimento: false });

const cartoesLocal = ref([]);
const showNewCard = ref(false);
const creatingCard = ref(false);
const newCard = reactive({
  nome: "",
  bandeira: "OUTRO",
  limite: null,
  dia_fechamento: 1,
  dia_vencimento: 10,
});
const bandeiraOptions = ["VISA", "MASTER", "ELO", "AMEX", "OUTRO"];

watch(
  () => props.cartoes,
  (arr) => {
    cartoesLocal.value = Array.isArray(arr) ? [...arr] : [];
  },
  { immediate: true }
);

function parseISODate(isoString) {
  if (!isoString) return new Date();
  const date = new Date(isoString);
  date.setMinutes(date.getMinutes() + date.getTimezoneOffset());
  return date;
}

/**
 * 🔧 Pré-preenchimento robusto para edição:
 * aceita tanto objetos completos quanto apenas IDs vindos do resumo.
 */
watch(
  () => [props.model, props.currentUserId, props.subcategorias],
  ([item, userId, subs]) => {
    const isEditing = item && item.id;

    if (isEditing) {
      local.id = item.id;

      // Detecta se é compra no cartão
      const isCard =
        item.type === "compra" ||
        !!item.compra_cartao ||
        !!item.compra_cartao_id ||
        !!item.parcelas_total ||
        !!item.parcela_numero;

      local.paymentMethod = isCard ? "card" : "cash";

      local.descricao = item.descricao ?? "";
      local.valor_total = item.valor_total ?? "";

      local.competencia = parseISODate(item.competencia);
      local.data_vencimento = parseISODate(
        item.data_vencimento || item.competencia
      );

      // Subcategoria/Categoria: aceita objeto ou id
      const subId = item.subcategoria?.id ?? item.subcategoria_id ?? null;
      local.subcategoria_id = subId;

      // tenta descobrir categoria a partir da subcategoria (quando vier só id)
      const subObj =
        item.subcategoria ??
        (Array.isArray(subs) ? subs.find((s) => s.id === subId) : null);

      local.categoria_id =
        item.subcategoria?.categoria?.id ??
        subObj?.categoria?.id ??
        subObj?.categoria_id ??
        null;

      local.escopo = item.escopo ?? "COMP";

      // Quem pagou / dono: aceita objeto ou id
      local.pagador_id = item.pagador?.id ?? item.pagador_id ?? userId ?? null;
      local.dono_pessoal_id =
        item.dono_pessoal?.id ?? item.dono_pessoal_id ?? null;

      local.status = item.status || "PENDENTE";

      // campos de cartão em edição (não obrigatório, mas neutros)
      local.cartao_id = item.cartao_id ?? null;
      local.parcelas_total = item.parcelas_total ?? 1;
    } else {
      // Novo
      local.id = null;
      local.paymentMethod = "cash";
      local.descricao = "";
      local.valor_total = "";
      local.competencia = new Date();
      local.data_vencimento = new Date();
      local.categoria_id = null;
      local.subcategoria_id = null;
      local.cartao_id = null;
      local.parcelas_total = 1;
      local.escopo = "COMP";
      local.pagador_id = userId;
      local.dono_pessoal_id = null;
      local.status = "PENDENTE";
    }
  },
  { immediate: true, deep: true }
);

// Segurança: ao trocar para "cash", limpa campos de cartão
watch(
  () => local.paymentMethod,
  (pm) => {
    if (pm === "cash") {
      local.cartao_id = null;
      local.parcelas_total = 1;
      showNewCard.value = false;
    }
  }
);

watch(
  () => local.escopo,
  (newEscopo) => {
    if (local.id) return;
    local.dono_pessoal_id = newEscopo === "PESS" ? props.currentUserId : null;
  }
);

function cancelNewCard() {
  showNewCard.value = false;
  Object.assign(newCard, {
    nome: "",
    bandeira: "OUTRO",
    limite: null,
    dia_fechamento: 1,
    dia_vencimento: 10,
  });
}

async function createCard() {
  if (!newCard.nome || !newCard.dia_vencimento || !newCard.dia_fechamento)
    return;
  creatingCard.value = true;
  try {
    const payload = { ...newCard };
    if (!payload.limite) delete payload.limite;
    const { data } = await axios.post("/cartoes/", payload);
    cartoesLocal.value.push(data);
    local.cartao_id = data.id;
    cancelNewCard();
  } catch (e) {
    console.error("Erro ao criar cartão:", e);
  } finally {
    creatingCard.value = false;
  }
}

const subcategoriasNormalizadas = computed(() =>
  (props.subcategorias || []).map((s) => ({
    ...s,
    categoria_id: s.categoria_id ?? s.categoria?.id ?? null,
  }))
);

const subcategoriasFiltradas = computed(() => {
  if (!local.categoria_id) return [];
  return subcategoriasNormalizadas.value.filter(
    (s) => s.categoria_id === local.categoria_id
  );
});

function onCategoriaChange() {
  const sub = subcategoriasNormalizadas.value.find(
    (s) => s.id === local.subcategoria_id
  );
  if (sub && sub.categoria_id !== local.categoria_id) {
    local.subcategoria_id = null;
  }
}

function toIsoDate(dateValue) {
  if (!dateValue) return null;
  const date = new Date(dateValue);
  if (isNaN(date.getTime())) return null;
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 10);
}

function formatBr(dateValue) {
  if (!dateValue) return "";
  const date = new Date(dateValue);
  if (isNaN(date.getTime())) return "";
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}

function emitSave() {
  const isCardPurchase = local.paymentMethod === "card" && !local.id;

  if (isCardPurchase) {
    emit("save", {
      descricao: local.descricao,
      valor_total: local.valor_total,
      subcategoria_id: local.subcategoria_id,
      cartao_id: local.cartao_id,
      parcelas_total: local.parcelas_total,
      primeira_competencia: toIsoDate(local.competencia),
      primeiro_vencimento: toIsoDate(local.data_vencimento),
      escopo: local.escopo,
      pagador_id: local.pagador_id,
      dono_pessoal_id: local.dono_pessoal_id,
      type: "compra",
    });
  } else {
    emit("save", {
      id: local.id,
      descricao: local.descricao,
      valor_total: local.valor_total,
      subcategoria_id: local.subcategoria_id,
      competencia: toIsoDate(local.competencia),
      data_vencimento: toIsoDate(local.data_vencimento),
      escopo: local.escopo,
      pagador_id: local.pagador_id,
      dono_pessoal_id: local.dono_pessoal_id,
      status: local.status,
      type: "lancamento",
    });
  }
}
</script>
