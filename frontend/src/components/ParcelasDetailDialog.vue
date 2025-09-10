<template>
  <v-dialog
    :model-value="show"
    persistent
    max-width="800px"
    @update:model-value="$emit('close')"
  >
    <v-card>
      <v-toolbar color="blue-darken-3" density="compact">
        <v-toolbar-title>Detalhe das Parcelas</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="$emit('close')">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-toolbar>

      <v-card-text v-if="compra">
        <v-list-item class="px-0">
          <v-list-item-title class="text-h6">{{
            compra.descricao
          }}</v-list-item-title>
          <v-list-item-subtitle>
            {{ formatCurrency(compra.valor_total) }} em
            {{ compra.parcelas_total }}x
          </v-list-item-subtitle>
        </v-list-item>
      </v-card-text>

      <v-card-text class="pt-0">
        <!-- Reutilizando o LancamentosList para mostrar as parcelas -->
        <LancamentosList
          :items="parcelas"
          :loading="loading"
          @edit="onEditParcela"
          @delete="onDeleteParcela"
          @quit="onQuitParcela"
        />
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="$emit('close')">Fechar</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from "vue";
import axios from "@/api/axios";
import LancamentosList from "@/components/LancamentosList.vue";

const props = defineProps({
  show: { type: Boolean, default: false },
  compra: { type: Object, default: null },
});

const emit = defineEmits([
  "close",
  "edit-parcela",
  "delete-parcela",
  "quit-parcela",
]);

const parcelas = ref([]);
const loading = ref(false);

watch(
  () => props.show,
  (newValue) => {
    if (newValue && props.compra?.id) {
      fetchParcelas();
    } else {
      parcelas.value = []; // Limpa ao fechar
    }
  }
);

async function fetchParcelas() {
  loading.value = true;
  try {
    // Usamos o filtro já existente no LancamentoViewSet
    const { data } = await axios.get("/lancamentos/", {
      params: { compra_cartao: props.compra.id },
    });
    parcelas.value = data?.results ?? data ?? [];
  } catch (error) {
    console.error("Erro ao buscar parcelas:", error);
    parcelas.value = [];
  } finally {
    loading.value = false;
  }
}

function formatCurrency(v) {
  const n = Number(v || 0);
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function onEditParcela(parcela) {
  emit("edit-parcela", parcela);
}
function onDeleteParcela(parcela) {
  emit("delete-parcela", parcela);
}
function onQuitParcela(parcela) {
  emit("quit-parcela", parcela);
}

// --- MUDANÇA AQUI ---
// Expõe a função fetchParcelas para que o componente pai possa chamá-la
defineExpose({
  fetchParcelas,
});
</script>
