import "./styles/main.css";
import App from './app.js';

const app = new App()

function ImageButtons(app) {
  this.app = app;

  this.randomButton = document.getElementById("random");
  this.randomButton.addEventListener("click", () => this.app.drawRandomImage());

  this.nextButton = document.getElementById("next");
  this.nextButton.addEventListener("click", () => this.app.drawNextImage());

  this.prevButton = document.getElementById("prev");
  this.prevButton.addEventListener("click", () => this.app.drawPrevImage());

  // FIXME temporary switch to usual confirm
  /*this.deleteButton = document.getElementById("confirmDelete");
  this.deleteButton.addEventListener("click", () => {
      console.log("del");
      $("#deleteModal").modal("hide");
      this.app.deleteImage();
    
  }); */
  this.deleteButton = document.getElementById("delete");
  this.deleteButton.addEventListener("click", () => {
    console.log("del");
    if (confirm("Are you sure to delete?")) {
      this.app.deleteImage();
    }
  });

  this.markButton = document.getElementById("mark");
  this.markButton.addEventListener("click", () => {
    if (!this.app.data.currentImage.marked) {
      this.app.markImage();
    }
  });
}

const panel = new ImageButtons(app);

