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
      <p class="title is-5">Current tag</p>
      <div class="columns is-multiline">
        <div class="column is-one-third">
          <TagCard :tag="current_tag"/>
        </div>
      </div>
    </div>
    <CreateTag v-if="showCreateTag" @close="showCreateTag = false"/>
  </section>
</template>

<script>
import CreateTag from './CreateTag.vue'
import TagCard from './TagCard.vue'

export default {
  name: 'TagList',
  components: {
    CreateTag, TagCard
  },
  data: function () {
    return {
      showCreateTag: false
    }
  },

  computed: {
    current_tag () {
      return this.$store.state.current_tag
    }
  },

  methods: {
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>
