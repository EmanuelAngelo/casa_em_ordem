<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Lançamentos</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="fetchLancamentos">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
        <v-btn prepend-icon="mdi-plus" @click="openForm()">
          Adicionar Lançamento
        </v-btn>
      </v-toolbar>

      <v-card-text>
        <LancamentosList
          :items="lancamentos"
          :loading="loading"
          @edit="openForm"
          @delete="confirmDelete"
          @quit="quitLancamento"
        />
      </v-card-text>
    </v-card>

    <!-- Dialog do Form -->
    <v-dialog v-model="dialog" persistent max-width="720px">
      <LancamentosForm
        :model="editedLancamento"
        :categorias="categorias"
        :membros="membrosOptions"
        :status-options="statusOptions"
        :escopo-options="escopoOptions"
        :saving="saving"
        @close="dialog = false"
        @save="saveLancamento"
      />
    </v-dialog>

    <!-- Confirmar Exclusão -->
    <v-dialog v-model="deleteDialog" persistent max-width="400px">
      <v-card>
        <v-card-title class="text-h5">Confirmar Exclusão</v-card-title>
        <v-card-text
          >Tem certeza que deseja excluir este lançamento?</v-card-text
        >
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="deleteDialog = false">Cancelar</v-btn>
          <v-btn color="red-darken-1" @click="deleteLancamentoConfirmed"
            >Excluir</v-btn
          >
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog de Erro -->
    <v-dialog v-model="errorDialog" persistent max-width="500px">
      <v-card>
        <v-card-title class="text-h5 bg-red-darken-2">
          <v-icon start icon="mdi-alert-circle-outline" />
          Operação Bloqueada
        </v-card-title>
        <v-card-text class="py-4 text-body-1">
          {{ errorMessage }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="blue-darken-1"
            variant="elevated"
            @click="errorDialog = false"
          >
            Entendi
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "@/api/axios";
import LancamentosList from "@/components/LancamentosList.vue";
import LancamentosForm from "@/components/LancamentosForm.vue";

const lancamentos = ref([]);
const categorias = ref([]);
const membrosOptions = ref([]);

const loading = ref(false);
const saving = ref(false);
const dialog = ref(false);
const deleteDialog = ref(false);

const editedLancamento = ref({});
const lancamentoToDelete = ref(null);

const errorDialog = ref(false);
const errorMessage = ref("");

const statusOptions = [
  { label: "Pendente", value: "PENDENTE" },
  { label: "Pago", value: "PAGO" },
  { label: "Cancelado", value: "CANCELADO" },
];
const escopoOptions = [
  { label: "Compartilhada", value: "COMP" },
  { label: "Pessoal", value: "PESS" },
];

const defaultLancamento = {
  categoria_id: null,
  escopo: "COMP",
  descricao: "",
  valor_total: "",
  competencia: new Date().toISOString().slice(0, 7) + "-01",
  data_vencimento: new Date().toISOString().slice(0, 7) + "-01",
  pagador_id: null,
  status: "PENDENTE",
  data_pagamento: "",
  dono_pessoal_id: null,
};

onMounted(async () => {
  await Promise.all([fetchCategorias(), fetchMembros()]);
  await fetchLancamentos();
});

const fetchLancamentos = async () => {
  loading.value = true;
  try {
    const resp = await axios.get("/lancamentos/");
    lancamentos.value = resp.data?.results ?? resp.data ?? [];
  } catch (error) {
    console.error("Erro ao buscar lançamentos:", error);
    errorMessage.value = "Não foi possível carregar os lançamentos.";
    errorDialog.value = true;
  } finally {
    loading.value = false;
  }
};

const fetchCategorias = async () => {
  const { data } = await axios.get("/categorias/");
  categorias.value = data;
};

const fetchMembros = async () => {
  const { data } = await axios.get("/casais/meu/");
  membrosOptions.value = (data?.membros || []).map((m) => ({
    label: m.usuario.first_name || m.usuario.username,
    value: m.usuario.id,
  }));
};

const openForm = (item = null) => {
  editedLancamento.value = item
    ? {
        id: item.id,
        categoria_id: item.categoria?.id ?? null,
        escopo: item.escopo,
        descricao: item.descricao,
        valor_total: String(item.valor_total ?? ""),
        competencia: item.competencia,
        data_vencimento: item.data_vencimento,
        pagador_id: item.pagador?.id ?? null,
        status: item.status,
        data_pagamento: item.data_pagamento || "",
        dono_pessoal_id: item.dono_pessoal?.id ?? null,
      }
    : {
        ...defaultLancamento,
        pagador_id: membrosOptions.value?.[0]?.value || null,
      };
  dialog.value = true;
};

const saveLancamento = async (payload) => {
  saving.value = true;
  try {
    const body = { ...payload };
    Object.keys(body).forEach(
      (k) => (body[k] === "" || body[k] === null) && delete body[k]
    );

    if (body.id) {
      await axios.patch(`/lancamentos/${body.id}/`, body);
    } else {
      await axios.post("/lancamentos/", body);
    }
    dialog.value = false;
    await fetchLancamentos();
  } catch (error) {
    console.error("Erro ao salvar lançamento:", error);
    errorMessage.value = "Não foi possível salvar o lançamento.";
    errorDialog.value = true;
  } finally {
    saving.value = false;
  }
};

const confirmDelete = (item) => {
  lancamentoToDelete.value = item;
  deleteDialog.value = true;
};

const deleteLancamentoConfirmed = async () => {
  try {
    await axios.delete(`/lancamentos/${lancamentoToDelete.value.id}/`);
    deleteDialog.value = false;
    await fetchLancamentos();
  } catch (error) {
    deleteDialog.value = false;
    errorMessage.value =
      error.response?.data?.detail ||
      "Ocorreu um erro ao excluir o lançamento.";
    errorDialog.value = true;
    console.error("Erro ao excluir lançamento:", error);
  }
};

const quitLancamento = async (item) => {
  try {
    await axios.post(`/lancamentos/${item.id}/quitar/`, {});
  } catch (error) {
    errorMessage.value = "Não foi possível quitar o lançamento.";
    errorDialog.value = true;
  } finally {
    await fetchLancamentos();
  }
};
</script>
