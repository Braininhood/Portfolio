#include <stdio.h>
#include <stdlib.h>
#include <time.h>

void runSortAndLog(const char *sortCmd, const char *inputFile, double *time_taken) {
    char command[256];
    snprintf(command, sizeof(command), "./%s %s", sortCmd, inputFile);

    // Start the timer
    clock_t start_time = clock();

    // Execute the sorting program
    system(command);

    // End the timer
    clock_t end_time = clock();
    *time_taken = (double)(end_time - start_time) / CLOCKS_PER_SEC;
}

int main() {
    // Files to test
    const char *files[] = {
        "random50000.txt", "random10000.txt", "random5000.txt"
    };
    int numFiles = sizeof(files) / sizeof(files[0]);

    // Sort programs to test
    const char *sortPrograms[] = {"sort1", "sort2", "sort3"};
    int numSorts = sizeof(sortPrograms) / sizeof(sortPrograms[0]);

    // Total times for sort1, sort2, sort3
    double total_sort1_time = 0.0;
    double total_sort2_time = 0.0;
    double total_sort3_time = 0.0;

    // Run sort1, sort2, sort3 on each file and record the time
    for (int i = 0; i < numFiles; i++) {
        double sort1_time, sort2_time, sort3_time;

        runSortAndLog("sort1", files[i], &sort1_time);
        runSortAndLog("sort2", files[i], &sort2_time);
        runSortAndLog("sort3", files[i], &sort3_time);

        total_sort1_time += sort1_time;
        total_sort2_time += sort2_time;
        total_sort3_time += sort3_time;
    }

    // Print total time for each sorting algorithm
    printf("Total time for sort1: %f seconds\n", total_sort1_time);
    printf("Total time for sort2: %f seconds\n", total_sort2_time);
    printf("Total time for sort3: %f seconds\n", total_sort3_time);

    // Open answers.txt for writing the analysis
    FILE *file = fopen("answers.txt", "w");
    if (file == NULL) {
        printf("Could not open answers.txt for writing.\n");
        return 1;
    }

    // Analyze the results and identify the sorting algorithms
    // Determine which sort is Merge Sort (min time), Selection Sort (max time), and Bubble Sort (in between)
    if (total_sort3_time < total_sort1_time && total_sort3_time < total_sort2_time) {
        fprintf(file, "sort3 uses: Merge Sort\n");
        fprintf(file, "How do you know?: Merge Sort has a time complexity of O(n log n), making it the fastest for large datasets.\n\n");

        if (total_sort1_time > total_sort2_time) {
            fprintf(file, "sort1 uses: Selection Sort\n");
            fprintf(file, "How do you know?: Selection Sort has O(n²) time complexity, which leads to the longest execution times.\n\n");
            fprintf(file, "sort2 uses: Bubble Sort\n");
            fprintf(file, "How do you know?: Bubble Sort's performance is typically worse than Selection Sort in many cases.\n\n");
        } else {
            fprintf(file, "sort1 uses: Bubble Sort\n");
            fprintf(file, "How do you know?: Bubble Sort shows worse performance than Selection Sort, confirming its expected O(n²) complexity.\n\n");
            fprintf(file, "sort2 uses: Selection Sort\n");
            fprintf(file, "How do you know?: Selection Sort takes the longest time among the sorts, confirming its O(n²) complexity.\n\n");
        }
    } else if (total_sort1_time < total_sort2_time && total_sort1_time < total_sort3_time) {
        fprintf(file, "sort1 uses: Merge Sort\n");
        fprintf(file, "How do you know?: Merge Sort is the fastest sorting algorithm, confirming its O(n log n) efficiency on larger datasets.\n\n");

        if (total_sort2_time > total_sort3_time) {
            fprintf(file, "sort2 uses: Selection Sort\n");
            fprintf(file, "How do you know?: Selection Sort has O(n²) time complexity, leading to slower performance.\n\n");
            fprintf(file, "sort3 uses: Bubble Sort\n");
            fprintf(file, "How do you know?: Bubble Sort typically performs worse than Merge Sort but can sometimes outperform Selection Sort.\n\n");
        } else {
            fprintf(file, "sort2 uses: Bubble Sort\n");
            fprintf(file, "How do you know?: Bubble Sort's performance indicates it is generally slower than Merge Sort but can outperform Selection Sort in specific cases.\n\n");
            fprintf(file, "sort3 uses: Selection Sort\n");
            fprintf(file, "How do you know?: Selection Sort takes the longest time among the sorts.\n\n");
        }
    } else {
        fprintf(file, "sort2 uses: Merge Sort\n");
        fprintf(file, "How do you know?: Merge Sort is the fastest sorting algorithm, confirming its O(n log n) efficiency on larger datasets.\n\n");

        if (total_sort1_time > total_sort3_time) {
            fprintf(file, "sort1 uses: Selection Sort\n");
            fprintf(file, "How do you know?: Selection Sort has O(n²) time complexity, which leads to the longest execution times.\n\n");
            fprintf(file, "sort3 uses: Bubble Sort\n");
            fprintf(file, "How do you know?: Bubble Sort's performance is typically worse than Selection Sort in many cases.\n\n");
        } else {
            fprintf(file, "sort1 uses: Bubble Sort\n");
            fprintf(file, "How do you know?: Bubble Sort shows worse performance than Selection Sort, confirming its expected O(n²) complexity.\n\n");
            fprintf(file, "sort3 uses: Selection Sort\n");
            fprintf(file, "How do you know?: Selection Sort takes the longest time among the sorts, confirming its O(n²) complexity.\n\n");
        }
    }

    // Close the file
    fclose(file);

    return 0;
}
