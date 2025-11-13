// AI Recipe Shoplist Crawler - Demo Functionality

class DemoManager {
  constructor(app) {
    this.app = app;
    this.apiBase = app.apiBase;
  }

  async loadDemo() {
    try {
      this.app.showLoading("Loading demo with Gazpacho recipe...");

      // Load demo search stores response
      const demoResponse = await fetch(`${this.apiBase}/demo`);
      const demoResult = await demoResponse.json();

      if (!demoResult.success) {
        throw new Error("Failed to load demo");
      }

      console.log("Demo data loaded:", demoResult);

      // Set demo shopping list items
      this.app.currentShoppingItems = demoResult.shopping_list_items || [];
      this.app.currentRecipe = this.createDemoRecipe();
      this.app.mapShoppingItemsToIngredients();

      // Display the demo results using custom rendering
      this.renderDemoResult(
        this.app.currentRecipe,
        this.app.currentShoppingItems
      );

      this.app.hideLoading();
    } catch (error) {
      console.error("Error loading demo:", error);
      this.app.showError(`Demo error: ${error.message}`);
      this.app.hideLoading();
    }
  }

  renderDemoResult(recipe, shoppingListItems) {
    const resultsSection = document.getElementById("resultsSection");
    const resultsContent = document.getElementById("resultsContent");
    if (!resultsSection || !resultsContent) return;

    const html = `
      <!-- Demo Banner -->
      <div class="alert alert-info">
        <h5><i class="fas fa-flask me-2"></i>Demo Mode - Gazpacho Recipe</h5>
        <p class="mb-0">This is a demo showing how the app works with pre-loaded product data from ALDI.</p>
      </div>

      <!-- Recipe Information -->
      <div class="recipe-card fade-in">
        <div class="recipe-title">
          <i class="fas fa-utensils me-2"></i>
          ${recipe.title}
        </div>
        <div class="recipe-meta">
          ${
            recipe.servings
              ? `<div class="meta-item"><i class="fas fa-users"></i> ${recipe.servings} servings</div>`
              : ""
          }
          ${
            recipe.prep_time
              ? `<div class="meta-item"><i class="fas fa-clock"></i> ${recipe.prep_time}</div>`
              : ""
          }
          ${
            recipe.cook_time
              ? `<div class="meta-item"><i class="fas fa-fire"></i> ${recipe.cook_time}</div>`
              : ""
          }
        </div>
        ${recipe.description ? `<p>${recipe.description}</p>` : ""}
        <a href="${
          recipe.url
        }" target="_blank" class="btn btn-outline-primary btn-sm">
          <i class="fas fa-external-link-alt me-1"></i>
          View Original Recipe
        </a>
      </div>

      <!-- Shopping List -->
      <div class="mb-4">
        <h5 class="mb-3">
          <i class="fas fa-shopping-basket me-2"></i>
          Shopping List
        </h5>
        <div class="ingredients-grid">
          ${this.renderShoppingList(shoppingListItems)}
        </div>
      </div>

      <!-- Instructions -->
      ${
        recipe.instructions && recipe.instructions.length > 0
          ? `
        <div class="mb-4">
          <h5 class="mb-3">
            <i class="fas fa-list-ol me-2"></i>
            Instructions
          </h5>
          <ol class="list-group list-group-numbered">
            ${recipe.instructions
              .map(
                (instruction) =>
                  `<li class="list-group-item">${instruction}</li>`
              )
              .join("")}
          </ol>
        </div>
      `
          : ""
      }

      <!-- Demo Summary -->
      <div class="alert alert-success">
        <h6><i class="fas fa-check-circle me-2"></i>Demo Complete!</h6>
        <p class="mb-2">This demo shows how the AI Recipe Shoplist Crawler:</p>
        <ul class="mb-0">
          <li>Extracts ingredients from recipes</li>
          <li>Finds matching products in grocery stores</li>
          <li>Provides direct links to store product pages</li>
          <li>Creates an organized shopping list</li>
        </ul>
      </div>
    `;

    resultsContent.innerHTML = html;
    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth" });
  }

  renderShoppingList(shoppingListItems) {
    return shoppingListItems
      .map((item) => {
        let ingredient = item.ingredient;
        // Fallback: if ingredient is a string, convert to object
        if (typeof ingredient === "string") {
          ingredient = { name: ingredient };
        }
        const product = item.selected_product;
        const quantityText = ingredient.quantity
          ? `${ingredient.quantity} ${ingredient.unit || ""}`.trim()
          : "As needed";
        const imageName = ingredient.name
          ? ingredient.name.replace(/\s+/g, "-").toLowerCase()
          : "unknown";
        const imageUrl = `/static/img/demo-pics/${imageName}.jpg`;
        const fallbackImage = this.app.generatePlaceholderImage(
          ingredient.name
        );
        const estimatedCost = item.estimated_cost || item.total_cost || null;
        return `
        <div class="ingredient-item">
          <div class="ingredient-image">
            <img src="${imageUrl}" alt="${
          ingredient.name
        }" class="img-fluid rounded" style="width: 80px; height: 80px; object-fit: cover;"
              onerror="this.src='${fallbackImage}'; this.onerror=null;">
          </div>
          <div class="ingredient-details flex-grow-1">
            <h6>${ingredient.name}</h6>
            <div class="ingredient-quantity">${quantityText}</div>
            <small class="text-muted">${ingredient.original_text || ""}</small>
            <div class="product-info">
              ${
                product
                  ? `
                <small class="text-success">
                  <i class="fas fa-store me-1"></i>
                  ${product.store || "Unknown Store"} - $${(
                      product.price || 0
                    ).toFixed(2)} ${product.price_unit || ""}
                </small>
                <br>
                ${
                  product.url
                    ? `<a href="${
                        product.url
                      }" target="_blank" class="text-decoration-none"><small class="text-primary"><i class="fas fa-external-link-alt me-1"></i>${
                        product.name || "Product name unavailable"
                      }</small></a>`
                    : `<small class="text-muted">${
                        product.name || "Product name unavailable"
                      }</small>`
                }
              `
                  : `
                <small class="text-warning">
                  <i class="fas fa-search me-1"></i>
                  No shopping products found
                </small>
              `
              }
            </div>
          </div>
          <div class="text-end">
            <strong class="text-success">${
              estimatedCost !== null ? `$${estimatedCost.toFixed(2)}` : "-"
            }</strong>
          </div>
        </div>
      `;
      })
      .join("");
  }

  createDemoRecipe() {
    return {
      title: "Gazpacho (Cold Spanish Soup)",
      url: "https://example.com/gazpacho-recipe",
      description: "A refreshing cold soup perfect for summer",
      servings: 4,
      prep_time: "20 minutes",
      cook_time: "0 minutes (no cooking required)",
      ingredients: [
        {
          name: "tomatoes",
          quantity: 4,
          unit: "piece",
          original_text: "4 large ripe tomatoes",
        },
        {
          name: "cucumber",
          quantity: 1,
          unit: "piece",
          original_text: "1 cucumber, peeled and diced",
        },
        {
          name: "garlic cloves",
          quantity: 2,
          unit: "clove",
          original_text: "2 cloves garlic, minced",
        },
        {
          name: "red onion",
          quantity: 0.5,
          unit: "piece",
          original_text: "1/2 red onion, finely chopped",
        },
        {
          name: "extra virgin olive oil",
          quantity: 60,
          unit: "ml",
          original_text: "4 tablespoons extra virgin olive oil",
        },
        {
          name: "sherry vinegar",
          quantity: 30,
          unit: "ml",
          original_text: "2 tablespoons sherry vinegar",
        },
        {
          name: "kosher salt",
          quantity: 1,
          unit: "tsp",
          original_text: "Salt to taste",
        },
        {
          name: "black pepper",
          quantity: 0.5,
          unit: "tsp",
          original_text: "Freshly ground black pepper",
        },
      ],
      instructions: [
        "Roughly chop the tomatoes, cucumber, and red onion",
        "Combine all vegetables in a large bowl",
        "Add garlic, olive oil, and sherry vinegar",
        "Season with salt and pepper",
        "Blend until smooth or leave chunky as preferred",
        "Chill in refrigerator for at least 2 hours",
        "Serve cold with a drizzle of olive oil",
      ],
    };
  }

  // displayDemoResults is no longer needed; main app display logic is used

  // renderDemoProducts is no longer needed; main app rendering is used
}
