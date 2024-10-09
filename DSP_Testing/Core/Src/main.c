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
#include "spi.h"
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
uint32_t dac_vals[BUFFERSIZE]; //dac buffer (may need to be larger for multiple output signals later
uint8_t data_ready;

//debug signals
uint16_t check;

// pointers to the half of the buffer being processed
static volatile uint32_t* input_buffer_ptr;
static volatile uint32_t* output_buffer_ptr = &dac_vals[0];

IIR2 low_12_1;
IIR2 low_12_2;

IIR2 high_12_1;
IIR2 high_12_2;

IIR2 low_30_1;
IIR2 low_30_2;

IIR2 high_30_1;
IIR2 high_30_2;


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
	output_buffer_ptr = &dac_vals[0];

	check = 2;

	data_ready = 1;
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
	input_buffer_ptr = &adc_vals[DATASIZE];
	output_buffer_ptr = &dac_vals[DATASIZE];

	check = 1;

	data_ready = 1;
}

void DSP(){

	float in12low;
	float out12low;

	float in12high;
	float out12high;

	float in30low;
	float out30low;

	float in30high;
	float out30high;

	for(int i = 0; i < DATASIZE; i++){
		in12low = (float) (input_buffer_ptr[i]);
		in12high = (float) (input_buffer_ptr[i]);
		in30low = (float) (input_buffer_ptr[i]);
		in30high = (float) (input_buffer_ptr[i]);

		out12low = IIR2_Update(&low_12_1, in12low);
		out12low = IIR2_Update(&low_12_2, out12low);

		out12high = IIR2_Update(&high_12_1, in12high);
		out12high = IIR2_Update(&high_12_2, out12high) * 2.5;

		out30low = IIR2_Update(&low_30_1, in30low);
		out30low = IIR2_Update(&low_30_2, out30low);

		out30high = IIR2_Update(&high_30_1, in30high);
		out30high = IIR2_Update(&high_30_2, out30high) * 2;


		output_buffer_ptr[i] = (uint32_t) (out12high);
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
  MX_SPI1_Init();
  MX_USB_PCD_Init();
  MX_ADC1_Init();
  MX_DAC_Init();
  MX_TIM6_Init();
  /* USER CODE BEGIN 2 */
  // START TIME BASE AND DMA CHANNELS
  HAL_TIM_Base_Start(&htim6);
  HAL_ADC_Start_DMA(&hadc1, (uint32_t *) adc_vals, BUFFERSIZE);
  HAL_DAC_Start_DMA(&hdac, DAC_CHANNEL_1, (uint32_t *) dac_vals, BUFFERSIZE, DAC_ALIGN_12B_R);

  // INIT FILTERS

  // 12 Hz low
  IIR2_Init(&low_12_1, -1.9931, 0.9931, 0.0595e-4, 0.1190e-4, 0.0595e-4);
  IIR2_Init(&low_12_2, -1.9929, 0.9930, 0.0997, -0.1993, 0.0997);

  // 12 Hz High
  IIR2_Init(&high_12_1, -1.9961, 0.9961, 0.9422, -1.8844, 0.9422);
  IIR2_Init(&high_12_2, -1.9990, 0.9990, 0.9221, -1.8442, 0.9221);

  // 30 Hz low
  IIR2_Init(&low_30_1, -1.9917, 0.9919, 0.5601, -1.1200, 0.5601);
  IIR2_Init(&low_30_2, -1.9879, 0.9881, 0.3144, -0.6286, 0.3144);

  // 30 Hz High
  IIR2_Init(&high_30_1, -1.9901, 0.9902, 0.9394, -1.8788, 0.9394);
  IIR2_Init(&high_30_2, -1.9863, 0.9865, 0.9163, -1.8326, 0.9163);

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
