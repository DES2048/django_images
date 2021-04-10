import { PickerSettings } from "../models";

// side navigation
export default class Sidenav {
  constructor(app) {
    this.app = app;

    // elements
    this.openButton = document.getElementById("sidenavOpen");
    this.closeButton = document.getElementById("sidenavClose");
    this.sidenav = document.getElementById("sidenav");
    this.saveButton = document.getElementById("btnSave");
    this.showMode = document.getElementById("showMode");
    this.gallsContainer = document.querySelector('#sidenav .galleries-container');

    // events listeners
    this.openButton.addEventListener("click", this.handleOpenSidenav.bind(this));
    this.closeButton.addEventListener("click", this.closeSidenav.bind(this));
    this.saveButton.addEventListener('click', this.handleSaveButton.bind(this));
    this.gallsContainer.addEventListener('click', this.handleGalleryClick.bind(this));
  }
  handleGalleryClick(event) {
    const elem = event.target;
    
    if (elem.tagName !=='A') {
      return
    }
    
    event.preventDefault();

    if (elem.classList.contains("selected")) {
      return;
    }
    const prevSelected = document.querySelector(
      ".galleries-container a.selected"
    );
    if (prevSelected) {
      prevSelected.classList.remove("selected");
    }
    elem.classList.add("selected");

  }
  redrawGalleriesList(galleries, selected_gallery) {
    this.gallsContainer.innerHTML = "";
    
    galleries.map((gallery) => {
      const elem = document.createElement("a");
      
      elem.innerHTML = gallery.title;
      elem.dataset.id = gallery.slug;
      
      if (gallery.slug == selected_gallery) {
        elem.classList.add("selected");
        elem.dataset.active = "true";
      }
      this.gallsContainer.append(elem);
    });
  }
  handleOpenSidenav(event) {
    this.sidenav.classList.add("sidenav-open");

    this.gallsContainer.innerHTML = "";

    Promise.all([this.app.getGalleries(), this.app.fetchSettings()]).then(
      (results) => {
        // draw galleries
        const galls = results[0];
        const settings = results[1];

        const selected_gallery = settings && settings.selected_gallery;
        const show_mode = settings && settings.show_mode;
        this.showMode.value = show_mode;

        this.redrawGalleriesList(galls, selected_gallery);
      }
    );
  }
  closeSidenav() {
    this.sidenav.classList.remove("sidenav-open");
  }
  handleSaveButton(event) {
    const settings = new PickerSettings(
      {
        show_mode: this.showMode.value,
        selected_gallery: document.querySelector(
          ".galleries-container a.selected"
        ).dataset.id,
      }
    );

    this.app
      .saveSettings(settings)
      .catch((error) => console.log(error.message))
      .finally(() => {
        this.closeSidenav();
      });
  }
}

