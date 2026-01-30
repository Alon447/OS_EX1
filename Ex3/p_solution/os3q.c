#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>

struct QItem {
	long val;
	struct QItem *next;
};

struct QueueOS {
	int max;
	long size; // not necessary
	long sum; // not necessary
	struct QItem *head;
	struct QItem *tail;

	pthread_mutex_t lock;
	pthread_cond_t	cv_full;
	pthread_cond_t 	cv_empty;
};

void queueos_init(struct QueueOS* q, int max) {
	q->head = NULL;
	q->tail = NULL;
	q->max = max;
	q->size = 0;
	q->sum = 0;
	
	// should check return values of all syscalls
	int rc;
	if ((rc = pthread_mutex_init(&q->lock, NULL)) != 0) {
		printf("pthread_mutex_init: %s\n", strerror(rc));
		exit(-1);
	}
	if ((rc = pthread_cond_init(&q->cv_empty, NULL)) != 0) {
		printf("pthread_cond_init cv_empty: %s\n", strerror(rc));
		exit(-1);
	}
	if ((rc = pthread_cond_init(&q->cv_full, NULL)) != 0) {
		printf("pthread_cond_init cv_full: %s\n", strerror(rc));
		exit(-1);
	}
}

void queueos_destroy(struct QueueOS* q) {
	// not ok if existing items are not freed (minor deduction)
	struct QItem *curr = q->head;
	while (curr != NULL) {
		struct QItem* tmp = curr;
		curr = curr->next;
		free(tmp);
	}

	// if remove() is called (until size==0) -- not ok if lock is grabbed
	// should be a minor deduction for performance

	// ok if return values aren't checked
	pthread_cond_destroy(&q->cv_empty);
	pthread_cond_destroy(&q->cv_full);
	pthread_mutex_destroy(&q->lock);
}


long queueos_size(struct QueueOS* q) {
	// ok if lock used to count items
	// NOT OK if lock used to read single value (minor deduction)
	return q->size;
}
long queueos_sum(struct QueueOS* q) {
	// ok if lock used to sum items
	// NOT OK if lock used to read single value (minor deduction)
	return q->sum;
}

long queueos_dequeue(struct QueueOS* q) {
	int rc;
	if ((rc = pthread_mutex_lock(&q->lock)) != 0) {
		printf("queueos_dequeue::pthread_mutex_lock: %s\n", strerror(rc));
		exit(-1);
	}

	// MUST block with cv WHILE queue is empty (major deduction)
	while (q->size == 0)
		pthread_cond_wait(&q->cv_full, &q->lock);
	
	struct QItem *item = q->head;
	q->head = q->head->next;
	if (q->head == NULL)
		q->tail = NULL;

	--q->size;
	q->sum -= item->val;

	// not ok if free() before release lock (minor deduction)
	if ((rc = pthread_mutex_unlock(&q->lock)) != 0) {
		printf("mylist_remove_head::pthread_mutex_unlock: %s\n", strerror(rc));
		exit(-1);
	}
	long val = item->val;

	// not ok if free before unlock() (minor deduction)
	free(item);

	// must signal - ok if signal() before unlock()
	if ((rc = pthread_cond_signal(&q->cv_empty)) != 0) {
		printf("mylist_remove_head::pthread_cond_signal: %s\n", strerror(rc));
		exit(-1);
	}

	return val;
}
void queueos_enqueue(struct QueueOS* q, long val) {
	// not ok if malloc after lock() (minor deduction)
	struct QItem *item = malloc(sizeof(struct QItem));
	if (item == NULL) {
		perror("queueos_enqueue malloc");
		exit(-1);
	}
	item->val = val;
	item->next = NULL;

	int rc;
	if ((rc = pthread_mutex_lock(&q->lock)) != 0) {
		printf("mylist_insert_tail::pthread_mutex_lock: %s\n", strerror(rc));
		exit(-1);
	}

	// MUST block with cv WHILE queue is full (major deduction)
	while (q->size == q->max)
		pthread_cond_wait(&q->cv_empty, &q->lock);
	if (q->tail != NULL) {
		q->tail->next = item;
	}
	else {
		q->head = item;
	}
	q->tail = item;

	++q->size;
	q->sum += val;

	if ((rc = pthread_mutex_unlock(&q->lock)) != 0) {
		printf("mylist_insert_tail::pthread_mutex_unlock: %s\n", strerror(rc));
		exit(-1);
	}

	// must signal - ok if signal() before unlock()
	if ((rc = pthread_cond_signal(&q->cv_full)) != 0) {
		printf("mylist_insert_tail::pthread_cond_signal: %s\n", strerror(rc));
		exit(-1);
	}
}

// submissions should not contain main() (major deduction / skip question)
int main(int argc, char *argv[])
{
	struct QueueOS q;
	queueos_init(&q, 10);
	printf("%ld %ld\n", queueos_size(&q), queueos_sum(&q));
	queueos_enqueue(&q, 5);
	queueos_enqueue(&q, 10);
	printf("%ld %ld\n", queueos_size(&q), queueos_sum(&q));
	printf("%ld\n", queueos_dequeue(&q));
	printf("%ld %ld\n", queueos_size(&q), queueos_sum(&q));
	printf("%ld\n", queueos_dequeue(&q));
	printf("%ld %ld\n", queueos_size(&q), queueos_sum(&q));
	queueos_destroy(&q);

	printf("Done.\n");
	return 0;
}
