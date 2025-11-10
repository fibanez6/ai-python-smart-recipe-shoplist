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

      // Set demo products and stores
      this.app.currentProducts = demoResult.products || [];

      // Map products to ingredients for display
      this.app.mapProductsToIngredients();

      // Create a demo recipe to match the products
      this.app.currentRecipe = this.createDemoRecipe();

      // Display the results directly since we have the products
      this.displayDemoResults({
        recipe: this.app.currentRecipe,
        products: this.app.currentProducts,
        stores: demoResult.stores || [],
      });

      this.app.hideLoading();
    } catch (error) {
      console.error("Error loading demo:", error);
      this.app.showError(`Demo error: ${error.message}`);
      this.app.hideLoading();
    }
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

  displayDemoResults(data) {
    const resultsSection = document.getElementById("resultsSection");
    const resultsContent = document.getElementById("resultsContent");

    if (!resultsSection || !resultsContent) return;

    const recipe = data.recipe;
    const products = data.products || [];

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

            <!-- Products Found -->
            <div class="mb-4">
                <h5 class="mb-3">
                    <i class="fas fa-shopping-basket me-2"></i>
                    Shopping List - Products Found (${products.length})
                </h5>
                <div class="ingredients-grid">
                    ${this.renderDemoProducts(products)}
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
                        (instruction) => `
                        <li class="list-group-item">${instruction}</li>
                    `
                      )
                      .join("")}
                </ol>
            </div>`
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

  renderDemoProducts(products) {
    return products
      .map((product) => {
        const productName = product.name || "Unknown Product";
        const ingredientName = product.ingredient || "Unknown Ingredient";
        const store = product.store || "Unknown Store";
        const price = product.price || 0;

        return `
                <div class="ingredient-item">
                    <div class="ingredient-image">
                        <img src="${
                          product.image_url ||
                          this.app.generatePlaceholderImage(ingredientName)
                        }" 
                             alt="${productName}" 
                             class="img-fluid rounded"
                             style="width: 80px; height: 80px; object-fit: cover;"
                             onerror="this.src='${this.app.generatePlaceholderImage(
                               ingredientName
                             )}'; this.onerror=null;">
                    </div>
                    <div class="ingredient-details flex-grow-1">
                        <h6>${ingredientName}</h6>
                        <div class="ingredient-quantity">${
                          product.quantity || 1
                        } ${product.size || "unit"}</div>
                        <small class="text-muted">${productName}</small>
                        <div class="product-info">
                            <small class="text-success">
                                <i class="fas fa-store me-1"></i>
                                ${store.toUpperCase()} - $${price.toFixed(2)}
                            </small>
                            ${
                              product.url
                                ? `<br><a href="${
                                    product.url
                                  }" target="_blank" class="text-decoration-none product-link">
                                   <small class="text-primary fw-bold">
                                     <i class="fas fa-external-link-alt me-1"></i>
                                     View at ${store.toUpperCase()}
                                   </small>
                                 </a>`
                                : ""
                            }
                            ${
                              product.ia_reasoning
                                ? `<br><small class="text-info">
                                   <i class="fas fa-robot me-1"></i>
                                   ${product.ia_reasoning}
                                 </small>`
                                : ""
                            }
                        </div>
                    </div>
                    <div class="text-end">
                        <strong class="text-success">$${price.toFixed(
                          2
                        )}</strong>
                    </div>
                </div>
            `;
      })
      .join("");
  }
}
