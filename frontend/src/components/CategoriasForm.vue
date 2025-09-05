<template>
  <v-card>
    <v-card-title class="text-h5">
      {{ model?.id ? "Editar Lançamento" : "Novo Lançamento" }}
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

          <v-col cols="12" md="6">
            <v-select
              v-model="local.escopo"
              :items="escopoOptions"
              item-title="label"
              item-value="value"
              label="Escopo"
              required
            />
          </v-col>

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

          <v-col cols="12" md="8">
            <v-text-field
              v-model="local.descricao"
              label="Descrição"
              prepend-inner-icon="mdi-text"
            />
          </v-col>

          <v-col cols="12" md="4">
            <v-select
              v-model="local.status"
              :items="statusOptions"
              item-title="label"
              item-value="value"
              label="Status"
              prepend-inner-icon="mdi-flag"
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-text-field
              v-model="local.competencia"
              label="Competência (YYYY-MM-01)"
              prepend-inner-icon="mdi-calendar"
              required
            />
          </v-col>

          <v-col cols="12" md="6">
            <v-text-field
              v-model="local.data_vencimento"
              label="Vencimento (YYYY-MM-DD)"
              prepend-inner-icon="mdi-calendar-alert"
              required
            />
          </v-col>

          <v-col cols="12" md="6" v-if="local.escopo === 'PESS'">
            <v-select
              v-model="local.dono_pessoal_id"
              :items="membros"
              item-title="label"
              item-value="value"
              label="Dono (pessoal)"
              prepend-inner-icon="mdi-account"
            />
          </v-col>

          <v-col cols="12" md="6">
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

          <v-col cols="12" md="6" v-if="local.status === 'PAGO'">
            <v-text-field
              v-model="local.data_pagamento"
              label="Data de pagamento (YYYY-MM-DD)"
              prepend-inner-icon="mdi-calendar-check"
            />
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
  categorias: { type: Array, default: () => [] }, // [{id, nome, ...}]
  subcategorias: { type: Array, default: () => [] }, // [{id, nome, categoria:{id,...}}] OU {categoria_id}
  membros: { type: Array, default: () => [] },
  statusOptions: { type: Array, default: () => [] },
  escopoOptions: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
});

const emit = defineEmits(["save", "close"]);

const local = reactive({
  id: null,
  categoria_id: null, // novo: escolha do grupo
  subcategoria_id: null, // novo: enviado ao backend
  escopo: "COMP",
  descricao: "",
  valor_total: "",
  competencia: "",
  data_vencimento: "",
  pagador_id: null,
  status: "PENDENTE",
  data_pagamento: "",
  dono_pessoal_id: null,
});

/** quando vier a lista de subcategorias no formato com categoria aninhada,
 *  normalizamos para ter 'categoria_id' para filtrar mais fácil.
 */
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

watch(
  () => props.model,
  (m) => {
    Object.assign(local, {
      id: m?.id ?? null,
      // Se o backend retornou subcategoria/categoria aninhados:
      categoria_id: m?.categoria?.id ?? null,
      subcategoria_id: m?.subcategoria?.id ?? null,
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

function onCategoriaChange() {
  // limpamos subcategoria se ela não pertencer ao novo grupo
  const match = subcategoriasNormalizadas.value.find(
    (s) => s.id === local.subcategoria_id
  );
  if (!match || match.categoria_id !== local.categoria_id) {
    local.subcategoria_id = null;
  }
}

function emitSave() {
  const payload = { ...local };
  // remove vazios
  Object.keys(payload).forEach(
    (k) => (payload[k] === "" || payload[k] === null) && delete payload[k]
  );
  // IMPORTANTE: backend usa subcategoria_id; categoria_id é só para UI (não precisa enviar)
  delete payload.categoria_id;
  emit("save", payload);
}
</script>
