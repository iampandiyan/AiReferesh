# 50 High-Priority Generative AI and AI/ML Principles MCQs for HirePro Assessment Preparation

**Q1. What is the primary characteristic that differentiates Generative AI from traditional Discriminative Machine Learning models?**
A) Generative AI models can only process text, whereas discriminative models process numbers.
B) Generative models learn the joint probability distribution $P(X, Y)$ or data distribution $P(X)$ to create new, original content, whereas discriminative models learn the conditional probability $P(Y|X)$ to classify or predict labels.
C) Generative models require no training data, unlike discriminative models.
D) Generative models are restricted to unsupervised linear regression tasks.
**Answer:** B
**Explanation:** Discriminative models map inputs to labels (classification/regression), while generative models capture the underlying data distribution to generate synthetic instances resembling the training set.

**Q2. In Large Language Models (LLMs), what is the function of "Tokenization"?**
A) Converting raw text strings into numerical identifiers (tokens) that map to embedding vectors.
B) Encrypting API requests for secure transmission.
C) Compressing model weights to fit into GPU memory.
D) Validating the syntax of generated Python code.
**Answer:** A
**Explanation:** Tokenization breaks raw text down into sub-words, words, or characters, which are then mapped to integer indices and converted into dense vector representations.

**Q3. What core architectural innovation introduced in the 2017 paper "Attention Is All You Need" forms the backbone of modern Generative AI models like GPT and LLaMA?**
A) Convolutional Neural Networks (CNNs)
B) Recurrent Neural Networks (RNNs) with LSTMs
C) The Transformer Architecture (Self-Attention Mechanism)
D) Support Vector Machines (SVM)
**Answer:** C
**Explanation:** The Transformer architecture entirely replaced recurrent layers with self-attention mechanisms, allowing parallel processing of sequential data and capturing long-range dependencies.

**Q4. What is the primary purpose of "Prompt Engineering" in working with LLMs?**
A) Compiling Python source code into machine bytecode.
B) Structuring input text and instructions to guide the model's latent capabilities and elicit accurate, context-specific responses without retraining weights.
C) Automatically tuning the hyperparameters of a neural network.
D) Encrypting user prompts to prevent data leaks.
**Answer:** B
**Explanation:** Prompt engineering guides an already-trained model via context, few-shot examples, and clear constraints to perform specific tasks effectively.

**Q5. What does RAG (Retrieval-Augmented Generation) solve in generative AI systems?**
A) It completely eliminates the need for neural networks.
B) It mitigates LLM hallucinations and provides access to private or up-to-date knowledge by retrieving relevant external documents and injecting them into the prompt context.
C) It compresses the token window size to speed up generation.
D) It converts unstructured text into relational database tables.
**Answer:** B
**Explanation:** RAG bridges the gap between parametric model memory and external data sources, querying a vector database to supply factual context during generation.

**Q6. What role do "Vector Embeddings" play in AI and machine learning systems?**
A) They store database connection strings securely.
B) They map high-dimensional data (like text, images, or audio) into dense numerical vectors where semantic similarity corresponds to spatial proximity (e.g., cosine similarity).
C) They act as software patches for LLM vulnerabilities.
D) They compile Python scripts into executable binaries.
**Answer:** B
**Explanation:** Embeddings translate conceptual meaning into multi-dimensional vectors, enabling mathematical operations like vector search and clustering based on semantic meaning.

**Q7. What is a "Vector Database" primarily optimized for?**
A) Relational ACID transactions and complex SQL joins.
B) High-throughput storage and rapid Approximate Nearest Neighbor (ANN) search over high-dimensional vector embeddings.
C) Compiling neural network training graphs.
D) Caching static web pages for content delivery networks.
**Answer:** B
**Explanation:** Vector databases (such as Pinecone, Milvus, or FAISS) use specialized indexing algorithms (like HNSW) to search through millions of embeddings in milliseconds.

**Q8. In reinforcement learning from human feedback (RLHF), what is the purpose of the Reward Model?**
A) To distribute cryptocurrency rewards to users who prompt the model.
B) To evaluate model outputs and score them based on human preferences for helpfulness, accuracy, and safety, guiding policy optimization (PPO).
C) To compress model weights during fine-tuning.
D) To tokenize incoming prompt sequences.
**Answer:** B
**Explanation:** The reward model simulates human judgment, scoring generated responses so the primary language model can be optimized via reinforcement learning.

**Q9. What is "Model Quantization" in deep learning?**
A) Scaling up the number of parameters from 7B to 70B.
B) Converting model weights from high-precision formats (like FP32 or FP16) to lower-precision formats (like INT8 or INT4) to reduce memory footprint and speed up inference.
C) Encrypting model weights to protect intellectual property.
D) Splitting a model across multiple GPUs.
**Answer:** B
**Explanation:** Quantization significantly reduces VRAM usage and speeds up inference with minimal degradation in model accuracy.

**Q10. What does "Temperature" control in LLM text generation?**
A) The physical operating temperature of the GPU hardware.
B) The randomness and creativity of the model's predictions by scaling logits before applying the softmax function.
C) The maximum number of tokens allowed in the response context.
D) The learning rate during model backpropagation.
**Answer:** B
**Explanation:** Higher temperature values flatten the probability distribution, leading to more creative and diverse outputs; lower temperatures make outputs deterministic and focused.

**Q11. What is a Generative Adversarial Network (GAN)?**
A) A database management framework for NoSQL clusters.
B) A machine learning framework where two neural networks—a Generator and a Discriminator—compete against each other, resulting in the generation of highly realistic synthetic data.
C) A cybersecurity tool for blocking prompt injection attacks.
D) A supervised classification model for email spam detection.
**Answer:** B
**Explanation:** Introduced by Ian Goodfellow, GANs pitch a generator (trying to fake data) against a discriminator (trying to spot fakes), co-evolving to produce realistic imagery or media.

**Q12. What are "Hallucinations" in Large Language Models?**
A) Hardware faults caused by overheating GPUs.
B) Confident generation of factually incorrect, fabricated, or nonsensical information presented as absolute truth by the model.
C) Visual glitches in AI-generated images.
D) Network timeout errors when querying an LLM API.
**Answer:** B
**Explanation:** LLMs predict token sequences based on statistical likelihood rather than factual grounding, which can lead to plausible-sounding falsehoods (hallucinations).

**Q13. What is the primary function of the "Model Context Protocol (MCP)" or function-calling capabilities in modern AI agents?**
A) To format responses strictly in XML.
B) To allow LLMs to securely invoke external tools, APIs, and databases dynamically during execution to fetch real-time data or execute actions.
C) To manage user session tokens in a web browser.
D) To compile Python code into WebAssembly.
**Answer:** B
**Explanation:** Function calling and protocols like MCP bridge static LLMs to dynamic external tools, turning models into active agents capable of interacting with software environments.

**Q14. What is "Fine-Tuning" in the context of machine learning?**
A) Adjusting the screen resolution of an AI-generated image.
B) Taking a pre-trained base model and further training it on a smaller, domain-specific dataset to adapt its behavior, style, or knowledge for specialized tasks.
C) Deleting redundant weights to clean up model storage.
D) Writing manual prompt instructions.
**Answer:** B
**Explanation:** Fine-tuning alters internal weights using supervised training data, making the model an expert in a specific domain compared to zero-shot base prompting.

**Q15. What is the difference between Zero-Shot, Few-Shot, and One-Shot prompting?**
A) Zero-shot uses no examples; One-shot uses a single example; Few-shot uses multiple examples in the prompt to guide the model's output pattern.
B) Zero-shot uses 0 GPUs; Few-shot uses multiple GPUs.
C) Zero-shot is for text; Few-shot is exclusively for image generation.
D) There is no functional difference.
**Answer:** A
**Explanation:** Shot-based prompting categorizes prompts by the number of demonstration examples provided in the context window to condition the model's response format and logic.

**Q16. What is an "Autoencoder" in neural networks?**
A) A model that automatically writes Python code.
B) An unsupervised neural network architecture trained to compress input data into a lower-dimensional latent space (encoding) and then reconstruct the original data as closely as possible (decoding).
C) A tool for automated database backups.
D) A chatbot framework for customer service.
**Answer:** B
**Explanation:** Autoencoders learn efficient representations (latent encodings) of input data, serving as the foundational concept behind Variational Autoencoders (VAEs).

**Q17. What is "Perplexity" when evaluating a language model?**
A) A measure of how confused the user is by the model's output.
B) A measurement of how well a probability model predicts a sample; lower perplexity indicates the model is less "surprised" by real-world text sequences.
C) The total number of parameters in billions.
D) The latency of an API response in milliseconds.
**Answer:** B
**Explanation:** Perplexity is a standard intrinsic evaluation metric in NLP used to quantify language model fluency and predictive accuracy on test corpora.

**Q18. What is "Overfitting" in machine learning?**
A) When a model trains too quickly and runs out of memory.
B) When a model learns the training data *too well*—including noise and outliers—resulting in excellent performance on training data but poor generalization to unseen test data.
C) When a dataset is too large for the GPU.
D) When the learning rate is set to zero.
**Answer:** B
**Explanation:** Overfitting compromises a model's real-world utility because it memorizes specific training samples instead of learning generalizable underlying patterns.

**Q19. What is the "Vanishing Gradient Problem" in deep neural networks?**
A) The loss of Wi-Fi connection during model training.
B) A phenomenon during backpropagation where gradients shrink exponentially as they approach earlier layers, preventing those layers from updating their weights effectively.
C) The gradual deletion of old training files.
D) A drop in GPU voltage during heavy workloads.
**Answer:** B
**Explanation:** Caused by activation functions like sigmoid or tanh across deep layers, vanishing gradients crippled early deep learning until innovations like ReLU and ResNets emerged.

**Q20. What is "Transfer Learning"?**
A) Moving files between AWS S3 buckets.
B) Reusing a pre-trained model (trained on a massive generic dataset) as the starting point for a new task on a different dataset, drastically reducing training time and data requirements.
C) Transferring ownership of an AI model to another company.
D) Converting PyTorch models to TensorFlow format.
**Answer:** B
**Explanation:** Transfer learning underpins modern AI; instead of training from scratch, developers build upon robust pre-trained foundation models.

**Q21. What is the purpose of the Softmax function in neural network classification layers?**
A) To soften the edges of AI-generated images.
B) To convert raw, unconstrained output scores (logits) from the final layer into a probability distribution that sums to 1 across mutually exclusive classes.
C) To compress network parameters.
D) To normalize input features before training.
**Answer:** B
**Explanation:** Softmax transforms arbitrary real-valued logit outputs into interpretable percentage probabilities for classification tasks.

**Q22. What is "Cross-Entropy Loss"?**
A) A measure of the network's energy consumption.
B) A loss function used in classification tasks that quantifies the difference between two probability distributions: the true labels and the predicted probabilities.
C) The cost of licensing commercial LLM APIs.
D) The time delay introduced by cross-region database replication.
**Answer:** B
**Explanation:** Cross-entropy loss penalizes confident wrong predictions heavily, driving effective optimization during backpropagation in classification and language models.

**Q23. What is "Latent Space" in generative models?**
A) The physical storage drive holding model checkpoints.
B) A multi-dimensional vector space where compressed representations (features and semantic concepts) of data points are organized and manipulated.
C) The delay between sending a prompt and receiving a response.
D) Unused RAM on a GPU cluster.
**Answer:** B
**Explanation:** Generative models manipulate points within a latent space to interpolate between concepts, generate novel variations, or alter image/text attributes.

**Q24. What is the primary benefit of using LoRA (Low-Rank Adaptation) for fine-tuning LLMs?**
A) It increases model size by 100x.
B) It freezes the original model weights and trains a small subset of rank decomposition matrices, drastically reducing GPU memory and storage requirements for fine-tuning.
C) It eliminates the need for tokenization.
D) It converts REST APIs into GraphQL.
**Answer:** B
**Explanation:** LoRA makes fine-tuning accessible on consumer or mid-tier enterprise hardware by updating only a fraction of the parameters.

**Q25. What is a "Diffusion Model" in generative AI?**
A) A model that spreads malware across cloud servers.
B) A generative framework that works by gradually adding Gaussian noise to training data (forward process) and then learning to reverse the noise process to generate structured data from pure noise (reverse process).
C) A model used for predicting stock market volatility.
D) A clustering algorithm for customer segmentation.
**Answer:** B
**Explanation:** Diffusion models (like Stable Diffusion and Midjourney) power state-of-the-art image and video generation by iteratively denoising latent representations.

**Q26. What does "In-Context Learning" mean for LLMs?**
A) Updating the model's permanent weights via gradient descent during inference.
B) The model's ability to adapt to tasks and patterns presented directly within its prompt window during inference without any weight updates.
C) Learning context from a connected SQL database.
D) Caching queries in Redis.
**Answer:** B
**Explanation:** Transformers process the entire prompt context simultaneously, allowing them to adapt dynamically to instructions or few-shot examples on the fly.

**Q27. What is the purpose of the "KV Cache" (Key-Value Cache) during LLM text generation?**
A) To cache user passwords for security.
B) To store previously computed attention keys and values for tokens across generation steps, preventing redundant matrix multiplications and speeding up token generation.
C) To save generated text files to disk.
D) To manage vector database indices.
**Answer:** B
**Explanation:** Without a KV cache, generating text autoregressively would require re-computing attention for the entire history at every single token step, slowing down inference drastically.

**Q28. What is "Model Drift" (or concept drift) in production machine learning systems?**
A) When a server physically shifts location in a datacenter.
B) The degradation of a model's predictive performance over time due to changes in real-world statistical properties, user behavior, or data distributions compared to training data.
C) The gradual reduction of model file size over time.
D) The migration from PyTorch to JAX.
**Answer:** B
**Explanation:** Real-world environments change; models deployed without monitoring will experience drift and declining accuracy as incoming data distributions diverge from training distributions.

**Q29. What is a "Transformer Decoder-only" architecture primarily designed for?**
A) Computer vision classification.
B) Autoregressive text generation tasks (predicting the next token given previous context, like GPT models).
C) Translating English images to French audio.
D) Relational database indexing.
**Answer:** B
**Explanation:** Decoder-only models use masked self-attention to generate text sequentially, dominating modern generative language modeling.

**Q30. What is "Adversarial Attack" in machine learning security?**
A) A cyberattack DDOSing an API endpoint.
B) Crafting subtle, malicious perturbations to input data (such as imperceptible pixel changes in an image or token tricks in text) designed to fool a model into making incorrect predictions.
C) Stealing database credentials via SQL injection.
D) Overloading GPU memory with large prompts.
**Answer:** B
**Explanation:** Adversarial inputs exploit vulnerabilities in decision boundaries, causing high-confidence misclassifications by machine learning models.

**Q31. What is "Self-Attention" in a Transformer model?**
A) A mechanism that lets the model evaluate the importance of different words in a sequence relative to each other, regardless of their positional distance.
B) A feature that allows the AI to monitor its own CPU usage.
C) An optimization algorithm that replaces gradient descent.
D) A security protocol for encrypting prompts.
**Answer:** A
**Explanation:** Self-attention computes attention scores between all token pairs in a sequence, allowing the model to capture complex contextual relationships instantly.

**Q32. What is "Beam Search" used for in text generation?**
A) Accelerating GPU clock speeds.
B) A decoding heuristic that explores multiple plausible token paths simultaneously and retains the top-K highest-probability sequences to avoid greedy decoding pitfalls.
C) Searching for vector embeddings in a database.
D) Compressing model weights.
**Answer:** B
**Explanation:** Unlike greedy search (which picks the single highest probability token at each step), beam search maintains a wider search tree to produce more coherent multi-token outputs.

**Q33. What is "Data Augmentation"?**
A) Deleting incomplete records from a dataset.
B) Artificially creating new training data by applying label-preserving transformations (such as rotation, cropping, or synonym substitution) to existing samples to improve model robustness.
C) Encrypting training data for privacy compliance.
D) Compressing CSV files into zip archives.
**Answer:** B
**Explanation:** Data augmentation expands limited training sets, helping models generalize better and reducing overfitting.

**Q34. What is the "Curse of Dimensionality"?**
A) The psychological stress of managing massive datasets.
B) Various phenomena that arise when analyzing and organizing data in high-dimensional spaces (like vector embeddings), where data becomes sparse and distance metrics lose discriminative power.
C) A bug in Python's numpy library.
D) The licensing cost of proprietary LLMs.
**Answer:** B
**Explanation:** In high dimensions, the volume of space grows exponentially, causing distance-based algorithms to degrade unless dimensionality reduction (like PCA) is used.

**Q35. What is "Principal Component Analysis (PCA)"?**
A) A deep learning architecture for text generation.
B) An unsupervised linear dimensionality reduction technique that transforms high-dimensional data into orthogonal variables called principal components while retaining maximum variance.
C) A database sharding algorithm.
D) An optimization method for gradient descent.
**Answer:** B
**Explanation:** PCA simplifies complex datasets by projecting them into fewer dimensions, helping visualize embeddings and remove multicollinearity.

**Q36. What is "Model Distillation" (Knowledge Distillation)?**
A) Filtering out toxic content from training corpora.
B) A model compression technique where a smaller, compact "student" model is trained to reproduce the behavior and output probability distributions of a large, complex "teacher" model.
C) Extracting source code from a compiled binary.
D) Splitting a monolithic database into microservices.
**Answer:** B
**Explanation:** Distillation allows developers to deploy fast, lightweight models in production while retaining a high percentage of a massive foundation model's performance.

**Q37. What is a "Decision Tree" in traditional machine learning?**
A) A flowchart-like structure where internal nodes represent feature tests, branches represent outcomes, and leaf nodes represent class labels or continuous values.
B) A neural network topology used in image processing.
C) A database indexing structure.
D) A version control branching strategy.
**Answer:** A
**Explanation:** Decision trees are interpretable supervised models that split data recursively based on feature thresholds.

**Q38. What is "Random Forest"?**
A) A neural network trained on botanical datasets.
B) An ensemble learning method that constructs a multitude of decision trees during training and outputs the mode (classification) or mean (regression) of the individual trees to improve generalization.
C) A cloud infrastructure provider for AI training.
D) A method for generating random vector embeddings.
**Answer:** B
**Explanation:** Random forests reduce overfitting and variance compared to single decision trees by averaging predictions across an ensemble of trees.

**Q39. What is "Gradient Boosting"?**
A) Increasing the voltage supplied to GPU clusters.
B) An ensemble technique that builds models sequentially, where each new model is trained to minimize the residual errors (gradients) made by the previous sequence of models (e.g., XGBoost, LightGBM).
C) A method for accelerating backpropagation.
D) A prompt engineering strategy.
**Answer:** B
**Explanation:** Gradient boosting algorithms dominate tabular machine learning competitions by iteratively correcting errors through sequential tree additions.

**Q40. What is an "Embedding Space Collapse" or degeneration problem in auto-regressive models?**
A) When a database server crashes.
B) A failure mode where the model repeats identical phrases or outputs degenerate, low-entropy token sequences endlessly.
C) When vector dimensions drop to zero.
D) A hardware failure in TPU clusters.
**Answer:** B
**Explanation:** Degeneration occurs when greedy decoding or poor penalty tuning causes models to get stuck in repetitive loops.

**Q41. What is "Semantic Search"?**
A) Searching for exact keyword matches in a SQL database table.
B) Searching for information based on the conceptual meaning, intent, and contextual context of a query rather than literal keyword matching, typically powered by vector embeddings.
C) Translating natural language to SQL queries.
D) Checking code syntax using regex.
**Answer:** B
**Explanation:** Semantic search understands synonyms and conceptual relations, returning relevant results even when search terms do not match document keywords literally.

**Q42. What is "Zero-Shot Classification"?**
A) Training a model without any data.
B) Using a pre-trained model to classify text into arbitrary labels it has never explicitly been trained or fine-tuned on, leveraging its general semantic understanding.
C) A classification algorithm that runs in 0 milliseconds.
D) Classifying images without labels.
**Answer:** B
**Explanation:** Foundation models can categorize text into unseen classes zero-shot by understanding the semantic definitions of those labels provided in the prompt.

**Q43. What is "Reinforcement Learning (RL)" distinguished by?**
A) Training exclusively on static CSV files.
B) An agent learning to make decisions by interacting with an environment, taking actions, and receiving rewards or penalties to maximize cumulative reward over time.
C) Requiring 100% human-labeled supervision for every step.
D) Operating without any reward signals.
**Answer:** B
**Explanation:** RL focuses on trial-and-error learning in dynamic environments, foundational for robotics, game-playing AI, and LLM alignment.

**Q44. What is the role of "Positional Encoding" in Transformer architectures?**
A) Tracking the GPS coordinates of user requests.
B) Injecting information about the relative or absolute position of tokens in the sequence, compensating for the Transformer's lack of inherent sequential awareness in self-attention.
C) Storing model weights in specific GPU memory addresses.
D) Formatting JSON output payloads.
**Answer:** B
**Explanation:** Because self-attention processes all tokens simultaneously without recurrence, positional encodings are added to token embeddings to preserve word order.

**Q45. What is "Model Pruning"?**
A) Deleting old training datasets from cloud storage.
B) Removing unnecessary or low-impact weights, neurons, or channels from a neural network to reduce model size and accelerate inference with minimal accuracy loss.
C) Truncating long prompts before sending them to an API.
D) Pruning branches from a decision tree.
**Answer:** B
**Explanation:** Pruning eliminates dead or redundant network parameters, creating leaner models for edge devices and high-throughput production environments.

**Q46. What is "Multimodal AI"?**
A) An AI that runs on multiple operating systems.
B) AI systems capable of processing, understanding, and reasoning across multiple data modalities simultaneously, such as text, images, audio, video, and code.
C) A model that uses multiple vector databases.
D) An ensemble of multiple language models.
**Answer:** B
**Explanation:** Modern foundation models (like GPT-4o and Gemini) are natively multimodal, seamlessly integrating visual, auditory, and textual understanding.

**Q47. What is "API Rate Limiting" in the context of deploying LLM applications?**
A) Limiting the physical speed of network cables.
B) Enforcing restrictions on the number of requests a client can send to an LLM endpoint within a specific timeframe to manage costs, prevent abuse, and ensure fair sharing of GPU resources.
C) Compressing API payloads.
D) Encrypting API keys.
**Answer:** B
**Explanation:** LLM inference is computationally expensive; rate limiting protects providers and applications from denial-of-service and budget overruns.

**Q48. What is "Synthetic Data Generation"?**
A) Copying data from competitor websites.
B) Using generative AI models (like GANs or LLMs) to artificially manufacture realistic training datasets when real-world data is scarce, expensive, or restricted by privacy regulations.
C) Generating fake user profiles for marketing.
D) Compressing real databases.
**Answer:** B
**Explanation:** Synthetic data is increasingly vital for training specialized AI models while maintaining data privacy and overcoming data scarcity.

**Q49. What is "AI Alignment"?**
A) Aligning server racks in a datacentre.
B) The research field focused on ensuring AI systems pursue goals, preferences, and ethical principles aligned with human intentions, safety, and values.
C) Aligning text formatting in Markdown outputs.
D) Synchronizing clocks across distributed GPU nodes.
**Answer:** B
**Explanation:** Alignment techniques (RLHF, constitutional AI) ensure powerful AI models remain safe, helpful, and honest.

**Q50. What is the primary function of an "AI Agent Framework" (such as LangChain, LlamaIndex, or CrewAI)?**
A) To replace relational databases entirely.
B) To provide abstractions, memory management, tool integration, and orchestration loops that allow LLMs to act autonomously over multi-step workflows to achieve complex goals.
C) To compile Python code into machine binaries.
D) To encrypt API endpoints.
**Answer:** B
**Explanation:** Agent frameworks combine LLMs with memory, planning loops, and external tools, enabling autonomous execution of multi-step engineering and business tasks.
