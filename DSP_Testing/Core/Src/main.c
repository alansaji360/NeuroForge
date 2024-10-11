/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2024 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dac.h"
#include "dma.h"
#include "i2c.h"
#include "tim.h"
#include "usb.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "EMA.h"
#include "notch.h"
#include "IIR.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
// # samples per data block(half buffer)
#define DATASIZE 128
// full buffer size
#define BUFFERSIZE DATASIZE * 2

//BUFFERS
uint32_t adc_vals[BUFFERSIZE]; //adc buffer
uint32_t alpha_vals[BUFFERSIZE]; //alpha buffer
uint32_t beta_vals[BUFFERSIZE]; //beta buffer
uint32_t gamma_vals[BUFFERSIZE]; //gamma buffer
uint8_t data_ready;

//debug signals
uint16_t check;

// pointers to the half of the buffer being processed
static volatile uint32_t* input_buffer_ptr;
static volatile uint32_t* alpha_buffer_ptr = &alpha_vals[0];
static volatile uint32_t* beta_buffer_ptr = &beta_vals[0];
static volatile uint32_t* gamma_buffer_ptr = &gamma_vals[0];

IIR1 high_8_1;
IIR1 high_8_2;
IIR1 high_8_3;

IIR1 low_12_1;
IIR1 low_12_2;
IIR1 low_12_3;

IIR2 high_12_1;
IIR2 high_12_2;

IIR2 low_30_1;
IIR2 low_30_2;

IIR2 high_30_1;
IIR2 high_30_2;

IIR2 low_100_1;
IIR2 low_100_2;


/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef* hadc)
{
	input_buffer_ptr = &adc_vals[0];

	alpha_buffer_ptr = &alpha_vals[0];
	beta_buffer_ptr = &beta_vals[0];
	gamma_buffer_ptr = &gamma_vals[0];

	data_ready = 1;
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
	input_buffer_ptr = &adc_vals[DATASIZE];

	alpha_buffer_ptr = &alpha_vals[DATASIZE];
	beta_buffer_ptr = &beta_vals[DATASIZE];
	gamma_buffer_ptr = &gamma_vals[DATASIZE];

	data_ready = 1;
}

void DSP(){

	float in8high;
	float out8high;

//	float in12low;
	float out12low;

	float in12high;
	float out12high;

//	float in30low;
	float out30low;

	float in30high;
	float out30high;

//	float in100low;
	float out100low;

	for(int i = 0; i < DATASIZE; i++){
		in8high = (float) (input_buffer_ptr[i]);
//		in12low = (float) (input_buffer_ptr[i]);
		in12high = (float) (input_buffer_ptr[i]);
//		in30low = (float) (input_buffer_ptr[i]);
		in30high = (float) (input_buffer_ptr[i]);
//		in100low = (float) (input_buffer_ptr[i]);

		out8high = IIR1_Update(&high_8_1, in8high);
		out8high = IIR1_Update(&high_8_2, out8high);
		out8high = IIR1_Update(&high_8_3, out8high) + 1500;

		out12low = IIR1_Update(&low_12_1, out8high);
		out12low = IIR1_Update(&low_12_2, out12low);
		out12low = IIR1_Update(&low_12_3, out12low);
		out12low *= 1.5;

		out12high = IIR2_Update(&high_12_1, in12high);
		out12high = IIR2_Update(&high_12_2, out12high) + 1500;
		out12high *= 1.1;

		out30low = IIR2_Update(&low_30_1, out12high);
		out30low = IIR2_Update(&low_30_2, out30low);

		out30high = IIR2_Update(&high_30_1, in30high);
		out30high = IIR2_Update(&high_30_2, out30high) + 1700;

		out100low = IIR2_Update(&low_100_1, out30high);
		out100low = IIR2_Update(&low_100_2, out100low) * 1.5;

		alpha_buffer_ptr[i] = (uint32_t) (out12low);
		beta_buffer_ptr[i] = (uint32_t) (out30low);
		gamma_buffer_ptr[i] = (uint32_t) (out100low);
	}
	data_ready = 0;
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */
  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_I2C1_Init();
  MX_USB_PCD_Init();
  MX_ADC1_Init();
  MX_DAC_Init();
  MX_TIM6_Init();
  /* USER CODE BEGIN 2 */
  // START TIME BASE AND DMA CHANNELS
  HAL_TIM_Base_Start(&htim6);
  HAL_ADC_Start_DMA(&hadc1, (uint32_t *) adc_vals, BUFFERSIZE);
  HAL_DAC_Start_DMA(&hdac, DAC_CHANNEL_1, (uint32_t *) gamma_vals, BUFFERSIZE, DAC_ALIGN_12B_R);
  HAL_DAC_Start_DMA(&hdac, DAC_CHANNEL_2, (uint32_t *) alpha_vals, BUFFERSIZE, DAC_ALIGN_12B_R);
  // INIT FILTERS
  // 8 Hz High
  IIR1_Init(&high_8_1, -0.9986, 0.9993, -0.9993);
  IIR1_Init(&high_8_2, -0.9986, 0.9993, -0.9993);
  IIR1_Init(&high_8_3, -0.9986, 0.9993, -0.9993);

  // 12 Hz low
  IIR1_Init(&low_12_1, -0.9925, 0.0038, 0.0038);
  IIR1_Init(&low_12_2, -0.9864, 0.0068, 0.0068);
  IIR1_Init(&low_12_3, -0.9898, 0.0051, 0.0051);

  // 12 Hz High
  IIR2_Init(&high_12_1, -1.9961, 0.9961, 0.9422, -1.8844, 0.9422);
  IIR2_Init(&high_12_2, -1.9990, 0.9990, 0.9221, -1.8442, 0.9221);

  // 30 Hz low
  IIR2_Init(&low_30_1, -1.9917, 0.9919, 0.5601, -1.1200, 0.5601);
  IIR2_Init(&low_30_2, -1.9879, 0.9881, 0.3144, -0.6286, 0.3144);

  // 30 Hz High
  IIR2_Init(&high_30_1, -1.9901, 0.9902, 0.9394, -1.8788, 0.9394);
  IIR2_Init(&high_30_2, -1.9863, 0.9865, 0.9163, -1.8326, 0.9163);

  // 100 Hz Low
  IIR2_Init(&low_100_1, -1.9626, 0.9645, 0.4390, -0.8762, 0.4390);
  IIR2_Init(&low_100_2, -1.9804, 0.9824, 0.9145, -1.8270, 0.9145);

  // a1, a2, b1, b2, b3
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
	  if(data_ready){
		  DSP();
	  }
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI|RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_BYPASS;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_USB|RCC_PERIPHCLK_I2C1
                              |RCC_PERIPHCLK_ADC12;
  PeriphClkInit.Adc12ClockSelection = RCC_ADC12PLLCLK_DIV1;
  PeriphClkInit.I2c1ClockSelection = RCC_I2C1CLKSOURCE_HSI;
  PeriphClkInit.USBClockSelection = RCC_USBCLKSOURCE_PLL_DIV1_5;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
