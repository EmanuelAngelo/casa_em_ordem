<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Modelos de Despesa</v-toolbar-title>
        <v-spacer />
        <v-btn icon @click="fetchAll">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
        <v-btn prepend-icon="mdi-plus" @click="openForm()">
          Adicionar Modelo
        </v-btn>
      </v-toolbar>

      <v-card-text>
        <DespesasModeloList
          :items="items"
          :loading="loading"
          @edit="openForm"
          @delete="confirmDelete"
        />
      </v-card-text>
    </v-card>

    <!-- Dialog Form -->
    <v-dialog v-model="dialog" persistent max-width="820px">
      <DespesasModeloForm
        :model="edited"
        :categorias="categorias"
        :membros="membrosOptions"
        :saving="saving"
        @close="dialog = false"
        @save="saveModelo"
      />
    </v-dialog>

    <!-- Confirmar Exclusão -->
    <v-dialog v-model="deleteDialog" persistent max-width="400px">
      <v-card>
        <v-card-title class="text-h5">Confirmar Exclusão</v-card-title>
        <v-card-text>Tem certeza que deseja excluir este modelo?</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Cancelar</v-btn>
          <v-btn color="red-darken-1" @click="deleteConfirmed">Excluir</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog de Erro -->
    <v-dialog v-model="errorDialog" persistent max-width="520px">
      <v-card>
        <v-card-title class="text-h5 bg-red-darken-2">
          <v-icon start icon="mdi-alert-circle-outline" />
          Erro
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

    <!-- Dialog de Sucesso simples (opcional) -->
    <v-snackbar v-model="snackbar.show" :timeout="2500">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from "vue";
import axios from "@/api/axios";
import DespesasModeloList from "@/components/DespesasModeloList.vue";
import DespesasModeloForm from "@/components/DespesasModeloForm.vue";

const items = ref([]);
const categorias = ref([]);
const membrosOptions = ref([]);

const loading = ref(false);
const saving = ref(false);
const dialog = ref(false);
const deleteDialog = ref(false);
const toDelete = ref(null);

const edited = ref({});

const errorDialog = ref(false);
const errorMessage = ref("");

const snackbar = ref({ show: false, text: "" });

onMounted(fetchAll);

async function fetchAll() {
  loading.value = true;
  try {
    const [cat, casal, modelos] = await Promise.all([
      axios.get("/categorias/"),
      axios.get("/casais/meu/"),
      axios.get("/despesas-modelo/"),
    ]);

    categorias.value = cat.data?.results ?? cat.data ?? [];
    membrosOptions.value =
      (casal.data?.membros || []).map((m) => ({
        label: m.usuario.first_name || m.usuario.username,
        value: m.usuario.id,
      })) ?? [];

    items.value = modelos.data?.results ?? modelos.data ?? [];
  } catch (e) {
    errorMessage.value = "Não foi possível carregar os dados.";
    errorDialog.value = true;
    console.error(e);
  } finally {
    loading.value = false;
  }
}

function openForm(item = null) {
  if (item) {
    edited.value = {
      id: item.id,
      nome: item.nome,
      categoria_id: item.categoria?.id ?? null,
      escopo: item.escopo,
      dono_pessoal_id: item.dono_pessoal?.id ?? null,
      valor_previsto: String(item.valor_previsto ?? ""),
      dia_vencimento: item.dia_vencimento ?? 1,
      recorrente: !!item.recorrente,
      periodicidade: item.periodicidade,
      regra_rateio: item.regra_rateio,
      ativo: !!item.ativo,
      // rateios_padrao chegam do backend para leitura:
      rateios: (item.rateios_padrao || []).map((r) => ({
        id: r.id,
        membro_id: r.membro?.id,
        percentual: r.percentual ?? null,
        valor_fixo: r.valor_fixo ?? null,
      })),
    };
  } else {
    edited.value = {
      id: null,
      nome: "",
      categoria_id: null,
      escopo: "COMP",
      dono_pessoal_id: null,
      valor_previsto: "",
      dia_vencimento: 1,
      recorrente: true,
      periodicidade: "MENSAL",
      regra_rateio: "IGUAL",
      ativo: true,
      rateios: [],
    };
  }
  dialog.value = true;
}

async function saveModelo(payload) {
  saving.value = true;
  try {
    const body = { ...payload };
    // limpa vazios
    Object.keys(body).forEach((k) => {
      if (body[k] === "" || body[k] === null) delete body[k];
    });

    let id = body.id;

    if (id) {
      await axios.patch(`/despesas-modelo/${id}/`, body);
    } else {
      const { data } = await axios.post("/despesas-modelo/", body);
      id = data.id;
    }

    // Sincroniza rateios padrão de forma simples:
    // 1) apaga todos os existentes
    // 2) recria a partir do formulário (se COMP e regra != IGUAL)
    if (body.escopo === "COMP" && body.regra_rateio !== "IGUAL") {
      // carrega os existentes
      const exist = await axios.get("/rateios-padrao/", {
        params: { despesa_modelo: id },
      });
      const existentes = exist.data?.results ?? exist.data ?? [];

      // apaga
      await Promise.all(
        existentes.map((r) => axios.delete(`/rateios-padrao/${r.id}/`))
      );

      // cria os novos
      const toCreate = (payload.rateios || []).filter(
        (r) =>
          r.membro_id &&
          ((body.regra_rateio === "PERCENTUAL" && r.percentual != null) ||
            (body.regra_rateio === "VALOR_FIXO" && r.valor_fixo != null))
      );

      await Promise.all(
        toCreate.map((r) =>
          axios.post("/rateios-padrao/", {
            despesa_modelo: id,
            membro_id: r.membro_id,
            percentual:
              body.regra_rateio === "PERCENTUAL" ? r.percentual : null,
            valor_fixo:
              body.regra_rateio === "VALOR_FIXO" ? r.valor_fixo : null,
          })
        )
      );
    } else {
      // se não for COMP ou for IGUAL, garante que não fiquem resquícios no backend
      const exist = await axios.get("/rateios-padrao/", {
        params: { despesa_modelo: id },
      });
      const existentes = exist.data?.results ?? exist.data ?? [];
      await Promise.all(
        existentes.map((r) => axios.delete(`/rateios-padrao/${r.id}/`))
      );
    }

    dialog.value = false;
    snackbar.value = { show: true, text: "Modelo salvo com sucesso!" };
    await fetchAll();
  } catch (e) {
    errorMessage.value =
      e.response?.data?.detail ||
      "Não foi possível salvar o modelo. Verifique os campos.";
    errorDialog.value = true;
    console.error(e);
  } finally {
    saving.value = false;
  }
}

function confirmDelete(item) {
  toDelete.value = item;
  deleteDialog.value = true;
}

async function deleteConfirmed() {
  try {
    await axios.delete(`/despesas-modelo/${toDelete.value.id}/`);
    deleteDialog.value = false;
    snackbar.value = { show: true, text: "Modelo excluído!" };
    await fetchAll();
  } catch (e) {
    deleteDialog.value = false;
    errorMessage.value =
      e.response?.data?.detail || "Não foi possível excluir o modelo.";
    errorDialog.value = true;
    console.error(e);
  }
}
</script>
