<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Lançamentos</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="fetchAllData">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
        <v-btn prepend-icon="mdi-plus" @click="openForm()">
          Adicionar Lançamento
        </v-btn>
      </v-toolbar>

      <v-card-text>
        <ComprasResumoList
          :items="lancamentosResumo"
          :loading="loading"
          @edit="openForm"
          @quit="quitLancamento"
          @view-details="openDetailsDialog"
        />
      </v-card-text>
    </v-card>

    <v-dialog v-model="formDialog" persistent max-width="720px">
      <LancamentosForm
        :model="editedItem"
        :categorias="categorias"
        :subcategorias="subcategorias"
        :membros="membrosOptions"
        :status-options="statusOptions"
        :escopo-options="escopoOptions"
        :cartoes="cartoes"
        :saving="saving"
        :current-user-id="currentUserId"
        @close="formDialog = false"
        @save="saveItem"
      />
    </v-dialog>

    <v-dialog v-model="formDialog" persistent max-width="720px">
      <LancamentosForm
        :model="editedItem"
        :categorias="categorias"
        :subcategorias="subcategorias"
        :membros="membrosOptions"
        :status-options="statusOptions"
        :escopo-options="escopoOptions"
        :cartoes="cartoes"
        :saving="saving"
        @close="formDialog = false"
        @save="saveItem"
      />
    </v-dialog>

    <!-- --- MUDANÇA AQUI: Adicionando a ref --- -->
    <ParcelasDetailDialog
      ref="parcelasDialogRef"
      :show="detailsDialog"
      :compra="selectedCompra"
      @close="detailsDialog = false"
      @edit-parcela="openForm"
      @delete-parcela="confirmDelete"
      @quit-parcela="quitLancamento"
    />

    <v-dialog v-model="deleteDialog" persistent max-width="400px">
      <v-card>
        <v-card-title class="text-h5">Confirmar Exclusão</v-card-title>
        <v-card-text>
          Tem certeza que deseja excluir esta parcela? Esta ação não pode ser
          desfeita.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="deleteDialog = false">Cancelar</v-btn>
          <v-btn color="red-darken-1" @click="deleteItemConfirmed">
            Excluir
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="errorDialog" persistent max-width="500px">
      <v-card>
        <v-card-title class="text-h5 bg-red-darken-2">
          <v-icon start icon="mdi-alert-circle-outline" />
          Operação Falhou
        </v-card-title>
        <v-card-text class="py-4 text-body-1" style="white-space: pre-wrap">
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
import LancamentosForm from "@/components/LancamentosForm.vue";
import ComprasResumoList from "@/components/ComprasResumoList.vue";
import ParcelasDetailDialog from "@/components/ParcelasDetailDialog.vue";

// --- MUDANÇA AQUI: Criando a ref para o dialog ---
const parcelasDialogRef = ref(null);

const lancamentosResumo = ref([]);
const categorias = ref([]);
const subcategorias = ref([]);
const membrosOptions = ref([]);
const cartoes = ref([]);
const currentUserId = ref(null);

const loading = ref(false);
const saving = ref(false);
const formDialog = ref(false);
const deleteDialog = ref(false);
const detailsDialog = ref(false);

const editedItem = ref({});
const itemToDelete = ref(null);
const selectedCompra = ref(null);

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

const defaultItem = {
  id: null,
  subcategoria_id: null,
  escopo: "COMP",
  descricao: "",
  valor_total: "",
  competencia: new Date(new Date().setDate(1)).toISOString().slice(0, 10),
  data_vencimento: new Date().toISOString().slice(0, 10),
  pagador_id: null,
  status: "PENDENTE",
  data_pagamento: null,
  dono_pessoal_id: null,
};

onMounted(fetchAllData);

async function fetchAllData() {
  loading.value = true;
  await Promise.all([
    fetchLancamentosResumo(),
    fetchCategorias(),
    fetchSubcategorias(),
    fetchMembros(),
    fetchCartoes(),
    fetchCurrentUser(),
  ]);
  loading.value = false;
}

async function fetchCurrentUser() {
  try {
    const { data } = await axios.get("/users/me/");
    currentUserId.value = data.id;
  } catch (e) {
    console.error("Não foi possível carregar os dados do usuário atual.", e);
    handleApiError(e, "Falha ao obter dados do usuário.");
  }
}

async function fetchLancamentosResumo() {
  try {
    const { data } = await axios.get("/lancamentos-resumo/");
    lancamentosResumo.value = data ?? [];
  } catch (error) {
    handleApiError(error, "Não foi possível carregar os lançamentos.");
  }
}

async function fetchCategorias() {
  try {
    const { data } = await axios.get("/categorias/");
    categorias.value = data?.results ?? data ?? [];
  } catch (error) {
    handleApiError(error, "Não foi possível carregar as categorias.");
  }
}

async function fetchSubcategorias() {
  try {
    const { data } = await axios.get("/subcategorias/");
    subcategorias.value = data?.results ?? data ?? [];
  } catch (error) {
    handleApiError(error, "Não foi possível carregar as subcategorias.");
  }
}

async function fetchMembros() {
  try {
    const { data } = await axios.get("/casais/meu/");
    membrosOptions.value = (data?.membros || []).map((m) => ({
      label: m.usuario.first_name || m.usuario.username,
      value: m.usuario.id,
    }));
    if (membrosOptions.value.length > 0) {
      defaultItem.pagador_id = membrosOptions.value[0].value;
    }
  } catch (error) {
    handleApiError(error, "Não foi possível carregar dados do casal.");
  }
}

async function fetchCartoes() {
  try {
    const { data } = await axios.get("/cartoes/");
    cartoes.value = data?.results ?? data ?? [];
  } catch (e) {
    cartoes.value = [];
    console.error("Não foi possível carregar os cartões.", e);
  }
}

function openForm(item = null) {
  editedItem.value = item ? { ...item } : { ...defaultItem };
  formDialog.value = true;
}

async function saveItem(payload) {
  saving.value = true;
  try {
    if (payload.usar_cartao && !payload.id) {
      const compraPayload = {
        cartao_id: payload.cartao_id,
        descricao: payload.descricao,
        subcategoria_id: payload.subcategoria_id,
        escopo: payload.escopo,
        dono_pessoal_id: payload.dono_pessoal_id,
        valor_total: payload.valor_total,
        parcelas_total: payload.parcelas_total,
        primeira_competencia: payload.competencia,
        primeiro_vencimento: payload.data_vencimento,
        pagador_id: payload.pagador_id,
      };
      Object.keys(compraPayload).forEach((key) => {
        if (compraPayload[key] === null || compraPayload[key] === undefined) {
          delete compraPayload[key];
        }
      });
      await axios.post("/compras-cartao/", compraPayload);
    } else {
      const url = payload.id ? `/lancamentos/${payload.id}/` : "/lancamentos/";
      const method = payload.id ? "patch" : "post";
      await axios[method](url, payload);
    }
    formDialog.value = false;
    await fetchAllData(); // Recarrega todos os dados para refletir mudanças
  } catch (error) {
    handleApiError(error, "Não foi possível salvar.");
  } finally {
    saving.value = false;
  }
}

function confirmDelete(item) {
  itemToDelete.value = item;
  deleteDialog.value = true;
}

async function deleteItemConfirmed() {
  try {
    await axios.delete(`/lancamentos/${itemToDelete.value.id}/`);
    deleteDialog.value = false;
    await fetchAllData();
  } catch (error) {
    handleApiError(error, "Erro ao excluir o item.");
  }
}

// --- MUDANÇA AQUI: Função de quitar atualizada ---
async function quitLancamento(item) {
  try {
    await axios.post(`/lancamentos/${item.id}/quitar/`, {});

    // Atualiza a lista principal de resumo
    await fetchLancamentosResumo();

    // Se o dialog de detalhes estiver aberto, chama sua função interna de refresh
    if (detailsDialog.value && parcelasDialogRef.value) {
      await parcelasDialogRef.value.fetchParcelas();
    }
  } catch (error) {
    handleApiError(error, "Não foi possível quitar a parcela.");
  }
}

function openDetailsDialog(compra) {
  selectedCompra.value = compra;
  detailsDialog.value = true;
}

function handleApiError(error, defaultMessage) {
  const responseData = error.response?.data;
  if (responseData && typeof responseData === "object") {
    errorMessage.value = Object.entries(responseData)
      .map(
        ([key, value]) =>
          `${key}: ${Array.isArray(value) ? value.join(", ") : value}`
      )
      .join("\n");
  } else {
    errorMessage.value = responseData || defaultMessage;
  }
  errorDialog.value = true;
}
</script>
