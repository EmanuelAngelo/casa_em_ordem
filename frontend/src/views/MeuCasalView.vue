<template>
  <v-container fluid>
    <v-card>
      <v-toolbar color="blue-darken-3">
        <v-toolbar-title>Meu Casal</v-toolbar-title>
        <v-spacer />
        <v-btn prepend-icon="mdi-lock" @click="passwordDialog = true">
          Alterar Senha
        </v-btn>
        <v-btn icon @click="loadCasal" :disabled="saving || loading"
          ><v-icon>mdi-refresh</v-icon></v-btn
        >
      </v-toolbar>

      <v-card-text>
        <v-skeleton-loader
          v-if="loading"
          type="article, actions"
        ></v-skeleton-loader>

        <!-- Estado 1: Usuário TEM um casal -->
        <v-row v-else-if="casal">
          <!-- Coluna Esquerda: Informações e Salários (agora se expande) -->
          <v-col cols="12" :lg="isCasalFull ? 12 : 6">
            <div>
              <v-text-field
                v-model="casal.nome"
                label="Nome do Casal"
                variant="outlined"
                density="compact"
                class="mb-4"
              />
              <v-list-subheader>Membros e Salários</v-list-subheader>
              <div
                v-for="membro in casal.membros"
                :key="membro.id"
                class="mb-3"
              >
                <v-text-field
                  v-model.number="membro.salario_mensal"
                  :label="`Salário de ${
                    membro.usuario.first_name || membro.usuario.username
                  }`"
                  type="number"
                  step="0.01"
                  prefix="R$"
                  variant="outlined"
                  density="compact"
                  hide-details
                />
              </div>
              <v-btn
                color="blue-darken-3"
                :loading="saving"
                @click="saveMembros"
                class="mt-2"
              >
                Salvar Alterações
              </v-btn>
            </div>
          </v-col>

          <!-- Coluna Direita: Convite (só aparece se o casal não estiver cheio) -->
          <v-col cols="12" lg="6" v-if="!isCasalFull">
            <v-card variant="outlined" class="fill-height">
              <v-card-title>Adicionar parceiro(a)</v-card-title>
              <v-card-subtitle
                >Adicione um usuário já cadastrado.</v-card-subtitle
              >
              <v-card-text>
                <v-form @submit.prevent="onInvite" :disabled="loadingInvite">
                  <v-text-field
                    v-model="usernameOrEmail"
                    label="Username ou e-mail"
                    prepend-inner-icon="mdi-account-plus"
                    required
                  />
                  <v-btn
                    color="blue-darken-3"
                    :loading="loadingInvite"
                    type="submit"
                  >
                    Adicionar
                  </v-btn>
                  <v-alert
                    v-if="inviteMsg"
                    class="mt-4"
                    :type="inviteType"
                    variant="tonal"
                  >
                    {{ inviteMsg }}
                  </v-alert>
                </v-form>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Estado 2: Usuário NÃO TEM um casal -->
        <v-alert v-else type="info" variant="tonal" class="pa-4 text-center">
          <h3 class="text-h6">Você ainda não faz parte de um casal!</h3>
          <p class="mt-2">
            Para começar, peça para seu parceiro(a) adicionar você (pelo seu
            username ou e-mail) ao casal dele(a).
          </p>
        </v-alert>
      </v-card-text>
    </v-card>

    <!-- DIALOG PARA ALTERAR SENHA -->
    <v-dialog v-model="passwordDialog" persistent max-width="500px">
      <v-card>
        <v-card-title>
          <span class="text-h5">Alterar Senha</span>
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="changePassword" :disabled="savingPassword">
            <v-text-field
              v-model="passwordForm.nova_senha"
              label="Nova Senha"
              type="password"
              prepend-inner-icon="mdi-lock"
              class="mb-2"
              :error-messages="passwordErrors.nova_senha"
              required
            />
            <v-text-field
              v-model="passwordForm.confirmacao_senha"
              label="Confirmar Nova Senha"
              type="password"
              prepend-inner-icon="mdi-lock-check"
              :error-messages="passwordErrors.confirmacao_senha"
              required
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="blue-darken-1"
            variant="text"
            @click="passwordDialog = false"
            >Cancelar</v-btn
          >
          <v-btn
            color="blue-darken-1"
            variant="text"
            :loading="savingPassword"
            @click="changePassword"
          >
            Salvar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="4000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from "vue";
import axios from "@/api/axios";

const casal = ref(null);
const loading = ref(true);
const saving = ref(false);
const loadingInvite = ref(false);
const usernameOrEmail = ref("");
const inviteMsg = ref("");
const inviteType = ref("info");
const snackbar = reactive({ show: false, text: "", color: "success" });

// --- Refs para o dialog de senha ---
const passwordDialog = ref(false);
const savingPassword = ref(false);
const passwordForm = reactive({ nova_senha: "", confirmacao_senha: "" });
const passwordErrors = ref({});

// --- Computed property para verificar se o casal está cheio ---
const isCasalFull = computed(() => {
  return casal.value && casal.value.membros && casal.value.membros.length >= 2;
});

onMounted(loadCasal);

async function loadCasal() {
  loading.value = true;
  try {
    const { data } = await axios.get("/casais/meu/");
    casal.value = data;
  } catch (e) {
    casal.value = null;
    console.error("Não foi possível carregar dados do casal:", e);
  } finally {
    loading.value = false;
  }
}

async function saveMembros() {
  if (!casal.value?.id) {
    snackbar.value = {
      show: true,
      text: "Erro: ID do casal não encontrado para salvar.",
      color: "error",
    };
    return;
  }
  saving.value = true;
  try {
    await axios.patch(`/casais/${casal.value.id}/`, { nome: casal.value.nome });
    const promises = casal.value.membros.map((membro) =>
      axios.patch(`/membros/${membro.id}/`, {
        salario_mensal: membro.salario_mensal || 0,
      })
    );
    await Promise.all(promises);
    snackbar.value = {
      show: true,
      text: "Dados do casal salvos com sucesso!",
      color: "success",
    };
  } catch (e) {
    console.error("Erro ao salvar dados do casal:", e);
    const detail =
      e.response?.data?.detail || "Erro ao salvar os dados. Tente novamente.";
    snackbar.value = { show: true, text: detail, color: "error" };
  } finally {
    saving.value = false;
  }
}

async function onInvite() {
  inviteMsg.value = "";
  inviteType.value = "info";
  loadingInvite.value = true;
  try {
    const { data } = await axios.post("/casais-extras/convidar/", {
      username_or_email: usernameOrEmail.value.trim(),
    });
    inviteMsg.value = data.detail || "Usuário adicionado ao casal.";
    inviteType.value = "success";
    usernameOrEmail.value = "";
    await loadCasal();
  } catch (e) {
    inviteMsg.value =
      e.response?.data?.detail || "Não foi possível adicionar o usuário.";
    inviteType.value = "error";
  } finally {
    loadingInvite.value = false;
  }
}

async function changePassword() {
  savingPassword.value = true;
  passwordErrors.value = {};
  try {
    const { data } = await axios.post("/auth/change-password/", passwordForm);
    snackbar.value = {
      show: true,
      text: data.detail || "Senha alterada!",
      color: "success",
    };
    passwordForm.nova_senha = "";
    passwordForm.confirmacao_senha = "";
    passwordDialog.value = false; // Fecha o dialog ao salvar
  } catch (e) {
    console.error("Erro ao alterar senha:", e);
    const errors = e.response?.data;
    if (errors && typeof errors === "object") {
      const firstErrorKey = Object.keys(errors)[0];
      const errorMessages = errors[firstErrorKey];
      const detail = Array.isArray(errorMessages)
        ? errorMessages[0]
        : errorMessages;
      snackbar.value = { show: true, text: detail, color: "error" };
      passwordErrors.value = errors;
    } else {
      snackbar.value = {
        show: true,
        text: "Não foi possível alterar a senha.",
        color: "error",
      };
    }
  } finally {
    savingPassword.value = false;
  }
}
</script>
