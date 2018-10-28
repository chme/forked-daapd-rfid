<template>
  <section class="section">
    <div class="container">
      <h1 class="title has-text-centered">
        Musicbox
      </h1>
      <article class="message is-warning">
        <div class="message-body">
          <p>
            Hold a Classic 1K MIFARE tag against the NFC reader Module (MFRC522) to see its contents.
            Press the <b>Create tag</b> button, if you want to create a new tag to start playing an album with forked-daapd.
          </p>
        </div>
      </article>
      <p class="content has-text-centered">
        <a class="button is-info is-outlined is-rounded" v-on:click="showCreateTag = true"><span class="icon"><i class="mdi mdi-tag-plus"></i></span> <span>Create tag!</span></a>
      </p>
      <p class="title is-5">Last tags</p>
      <div class="columns is-multiline">
        <div class="column is-one-quarter" v-for="tag in tags" :key="tag.id">
          <TagCard :tag="tag"/>
        </div>
      </div>
    </div>
    <CreateTag v-if="showCreateTag" @close="showCreateTag = false"/>
  </section>
</template>

<script>
import CreateTag from './CreateTag.vue'
import TagCard from './TagCard.vue'
import axios from 'axios'

export default {
  name: 'TagList',
  components: {
    CreateTag, TagCard
  },
  data: function () {
    return {
      showCreateTag: false,
      tags: []
    }
  },
  created: function () {
    this.loadTags()
  },

  methods: {
    loadTags: function () {
      axios.get('/api/tags').then(({ data }) => {
        this.tags = data.tags
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
