<template>
  <v-card>
    <v-card-title class="text-h5">
      {{ model?.id ? "Editar Categoria" : "Nova Categoria" }}
    </v-card-title>

    <v-card-text>
      <v-form @submit.prevent="emitSave" :disabled="saving">
        <v-row dense>
          <v-col cols="12" md="8">
            <v-text-field
              v-model="local.nome"
              label="Nome"
              prepend-inner-icon="mdi-tag-text-outline"
              required
            />
          </v-col>

          <v-col cols="12" md="4" class="d-flex align-center">
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
import { reactive, watch } from "vue";

const props = defineProps({
  model: { type: Object, default: () => ({}) },
  saving: { type: Boolean, default: false },
});
const emit = defineEmits(["save", "close"]);

const local = reactive({ id: null, nome: "", ativa: true });

watch(
  () => props.model,
  (m) => {
    Object.assign(local, {
      id: m?.id ?? null,
      nome: m?.nome ?? "",
      ativa: m?.ativa ?? true,
    });
  },
  { immediate: true, deep: true }
);

function emitSave() {
  emit("save", { ...local });
}
</script>
