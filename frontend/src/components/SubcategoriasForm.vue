<template>
  <v-card>
    <v-card-title class="text-h5">
      {{ model?.id ? "Editar Subcategoria" : "Nova Subcategoria" }}
    </v-card-title>

    <v-card-text>
      <v-form @submit.prevent="emitSave" :disabled="saving">
        <v-row dense>
          <v-col cols="12" md="7">
            <v-text-field
              v-model="local.nome"
              label="Nome"
              prepend-inner-icon="mdi-tag-outline"
              required
            />
          </v-col>

          <v-col cols="12" md="5">
            <v-select
              v-model="local.categoria_id"
              :items="categoriasItems"
              item-title="nome"
              item-value="id"
              label="Categoria (grupo)"
              prepend-inner-icon="mdi-folder-outline"
              :disabled="lockedCategoria"
              required
            />
          </v-col>

          <v-col cols="12" class="d-flex align-center">
            <v-switch
              v-model="local.ativa"
              label="Ativa"
              color="blue-darken-3"
              hide-details
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
import { reactive, watch, computed } from "vue";

const props = defineProps({
  model: { type: Object, default: () => ({}) },
  categorias: { type: Array, default: () => [] }, // [{id, nome}]
  saving: { type: Boolean, default: false },
  lockedCategoria: { type: Boolean, default: false },
});
const emit = defineEmits(["save", "close"]);

const categoriasItems = computed(() => {
  if (!props.lockedCategoria) return props.categorias;
  const id = local.categoria_id;
  return props.categorias.filter((c) => c.id === id);
});

const local = reactive({
  id: null,
  nome: "",
  categoria_id: null,
  ativa: true,
});

watch(
  () => props.model,
  (m) => {
    Object.assign(local, {
      id: m?.id ?? null,
      nome: m?.nome ?? "",
      categoria_id: m?.categoria?.id ?? m?.categoria_id ?? null,
      ativa: m?.ativa ?? true,
    });
  },
  { immediate: true, deep: true }
);

function emitSave() {
  const payload = { ...local };
  Object.keys(payload).forEach(
    (k) => (payload[k] === "" || payload[k] === null) && delete payload[k]
  );
  emit("save", payload);
}
</script>
