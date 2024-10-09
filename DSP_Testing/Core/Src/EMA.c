/*
 * EMA.c
 *
 *  Created on: Sep 18, 2024
 *      Author: akarl
 */

#include "EMA.h"

void EMA_Init(EMA *filter, float alpha){
	filter->alpha = 0.0;
	EMA_SetAlpha(filter, alpha);

	filter->out = 6.0;
}

void EMA_SetAlpha(EMA *filter, float alpha){
	if(alpha > 1.0){
		alpha = 1.0;
	}
	else if(alpha < 0.0){
		alpha = 0.0;
	}

	filter->alpha = alpha;
}

float EMA_Update(EMA *filter, float input){
	filter->out = filter->alpha * input + (1.0 - filter->alpha) * filter->out;

	return filter->out;
}
