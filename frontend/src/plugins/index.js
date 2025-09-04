import vuetify from "./vuetify";
import { createPinia } from "pinia";
import router from "@/router";

export default function install(app) {
  app.use(vuetify);
  app.use(createPinia());
  app.use(router);
}
