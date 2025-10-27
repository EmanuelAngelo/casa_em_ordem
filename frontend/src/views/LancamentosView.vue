<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Lançamentos</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="fetchAllData">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
        <v-btn
          prepend-icon="mdi-credit-card-multiple"
          @click="openComprasDialog"
        >
          Compras no cartão
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
          @view-details="openDetailsFromList"
        />
      </v-card-text>
    </v-card>

    <!-- Formulário -->
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

    <!-- Detalhes / Parcelas -->
    <ParcelasDetailDialog
      ref="parcelasDialogRef"
      :show="detailsDialog"
      :compra="selectedCompra"
      @close="detailsDialog = false"
      @edit-parcela="openForm"
      @delete-parcela="confirmDelete"
      @quit-parcela="quitLancamento"
    />

    <!-- Lista de Compras no Cartão -->
    <v-dialog v-model="comprasDialog" max-width="1000px">
      <v-card>
        <v-toolbar color="blue-darken-3" density="comfortable">
          <v-toolbar-title>Compras no cartão</v-toolbar-title>
          <v-spacer />
          <v-btn icon :loading="comprasLoading" @click="fetchComprasCartao">
            <v-icon>mdi-refresh</v-icon>
          </v-btn>
          <v-btn icon @click="comprasDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>

        <v-card-text>
          <ComprasCartaoList
            :items="comprasCartao"
            :loading="comprasLoading"
            @view-details="openDetailsFromCompras"
          />
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Confirmar exclusão -->
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

    <!-- Erros -->
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
import { ref, onMounted, nextTick } from "vue";
import axios from "@/api/axios";
import LancamentosForm from "@/components/LancamentosForm.vue";
import ComprasResumoList from "@/components/ComprasResumoList.vue";
import ParcelasDetailDialog from "@/components/ParcelasDetailDialog.vue";
import ComprasCartaoList from "@/components/ComprasCartaoList.vue";

const parcelasDialogRef = ref(null);

const lancamentosResumo = ref([]);
const categorias = ref([]);
const subcategorias = ref([]);
const membrosOptions = ref([]);
const cartoes = ref([]);

const comprasDialog = ref(false);
const comprasLoading = ref(false);
const comprasCartao = ref([]);

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
  ]);
  loading.value = false;
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
    const { data } = await axios.get("/grupos/meu/");
    membrosOptions.value = (data?.membros || []).map((m) => ({
      label: m.usuario.first_name || m.usuario.username,
      value: m.usuario.id,
    }));
    if (membrosOptions.value.length > 0) {
      defaultItem.pagador_id = membrosOptions.value[0].value;
    }
  } catch {
    // ok sem grupo
  }
}

async function fetchCartoes() {
  try {
    const { data } = await axios.get("/cartoes/");
    cartoes.value = data?.results ?? data ?? [];
  } catch {
    cartoes.value = [];
  }
}

function openForm(item = null) {
  editedItem.value = item ? { ...item } : { ...defaultItem };
  formDialog.value = true;
}

/** Diálogo "Compras no cartão" */
function openComprasDialog() {
  comprasDialog.value = true;
  fetchComprasCartao();
}

/** Lista de compras parceladas */
async function fetchComprasCartao() {
  comprasLoading.value = true;
  try {
    const { data } = await axios.get("/compras-cartao/");
    comprasCartao.value = Array.isArray(data) ? data : data?.results ?? [];
  } catch (error) {
    handleApiError(error, "Não foi possível carregar as compras no cartão.");
    comprasCartao.value = [];
  } finally {
    comprasLoading.value = false;
  }
}

/**
 * Salvar (cartão => /compras-cartao/, cash => /lancamentos/)
 */
async function saveItem(payload) {
  saving.value = true;
  try {
    const isCard = payload?.type === "compra" || payload?.usar_cartao === true;

    if (isCard && !payload.id) {
      const compraPayload = {
        cartao_id: payload.cartao_id,
        descricao: payload.descricao,
        subcategoria_id: payload.subcategoria_id,
        escopo: payload.escopo,
        dono_pessoal_id: payload.dono_pessoal_id || null,
        valor_total: payload.valor_total,
        parcelas_total: payload.parcelas_total,
        primeira_competencia:
          payload.primeira_competencia || payload.competencia,
        primeiro_vencimento:
          payload.primeiro_vencimento || payload.data_vencimento,
        pagador_id: payload.pagador_id,
      };
      Object.keys(compraPayload).forEach((k) => {
        if (compraPayload[k] == null) delete compraPayload[k];
      });

      const { data: compraCriada } = await axios.post(
        "/compras-cartao/",
        compraPayload
      );

      formDialog.value = false;

      // Atualiza listas e mostra detalhes da compra criada
      await Promise.all([fetchLancamentosResumo(), fetchComprasCartao()]);
      await openDetailsByCompraId(compraCriada.id);
    } else {
      const lancPayload = {
        id: payload.id || null,
        descricao: payload.descricao,
        subcategoria_id: payload.subcategoria_id,
        competencia: payload.competencia,
        data_vencimento: payload.data_vencimento,
        escopo: payload.escopo,
        pagador_id: payload.pagador_id,
        dono_pessoal_id: payload.dono_pessoal_id || null,
        status: payload.status || "PENDENTE",
        valor_total: payload.valor_total,
      };
      delete lancPayload.type;

      const url = lancPayload.id
        ? `/lancamentos/${lancPayload.id}/`
        : "/lancamentos/";
      const method = lancPayload.id ? "patch" : "post";
      await axios[method](url, lancPayload);

      formDialog.value = false;
      await fetchAllData();
    }
  } catch (error) {
    handleApiError(error, "Não foi possível salvar.");
  } finally {
    saving.value = false;
  }
}

/** Abre detalhes vindo do RESUMO (resolve o compraId antes) */
async function openDetailsFromList(item) {
  // Tenta extrair o ID da compra a partir do item do resumo
  const compraId =
    item?.raw?.compra_cartao?.id ||
    item?.raw?.compra_cartao_id ||
    item?.compra_cartao?.id ||
    item?.compra_cartao_id ||
    null;

  if (!compraId) {
    // se não existe compra ligada, não abre
    return;
  }
  await openDetailsByCompraId(compraId);
}

/** Abre detalhes vindo da LISTA DE COMPRAS (item já é compra, mas garantimos o detalhe) */
async function openDetailsFromCompras(item) {
  const compraId = item?.id;
  if (!compraId) return;
  await openDetailsByCompraId(compraId);
}

/** Carrega o detalhe da compra e abre o diálogo; depois pede pro diálogo recarregar as parcelas */
async function openDetailsByCompraId(compraId) {
  try {
    const { data } = await axios.get(`/compras-cartao/${compraId}/`);
    selectedCompra.value = data;
    detailsDialog.value = true;

    await nextTick();
    if (parcelasDialogRef.value?.fetchParcelas) {
      await parcelasDialogRef.value.fetchParcelas();
    }
  } catch (error) {
    handleApiError(error, "Não foi possível abrir os detalhes da compra.");
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

async function quitLancamento(item) {
  try {
    await axios.post(`/lancamentos/${item.id}/quitar/`, {});
    await fetchLancamentosResumo();

    if (detailsDialog.value && parcelasDialogRef.value?.fetchParcelas) {
      await parcelasDialogRef.value.fetchParcelas();
    }
  } catch (error) {
    handleApiError(error, "Não foi possível quitar a parcela.");
  }
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
