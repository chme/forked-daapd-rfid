import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    conf: {
      'server': ''
    }
  },

  getters: {
  },

  mutations: {
    setConf (state, conf) {
      state.conf = conf
    }
  },

  actions: {
  }
})
